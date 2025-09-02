import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "@/hooks/use-toast";
import Login from "./Login";
import {
  Brain,
  Upload,
  Book,
  BarChart3,
  Search,
  Edit,
  Settings,
  Plus,
  FileText,
  Check,
  X,
  Eye,
  FileUp,
  Save,
  Trash2,
  Download
} from "lucide-react";

// Types
interface Subject {
  id: string;
  name: string;
  createdAt: string;
  schemeFile?: {
    name: string;
    content: string;
    uploadedAt: string;
  };
}

interface EvaluationResult {
  id: string;
  studentName: string;
  studentId: string;
  subject: string;
  fileName: string;
  marks: number;
  maxMarks: number;
  percentage: number;
  passed: boolean;
  uploadedAt: string;
  evaluatedAt: string;
  comments?: string;
  manuallyEvaluated?: boolean;
}

interface UploadedFile {
  fileName: string;
  content: string;
  subject: string;
  studentName: string;
  studentId: string;
  resultId: string;
}

interface AppState {
  subjects: Subject[];
  results: EvaluationResult[];
  uploadedFiles: UploadedFile[];
}

// Utility functions
const generateId = () => Math.random().toString(36).substr(2, 9);

const saveToStorage = (data: AppState) => {
  localStorage.setItem('evalai_pro_data', JSON.stringify(data));
};

const loadFromStorage = (): AppState => {
  try {
    const stored = localStorage.getItem('evalai_pro_data');
    return stored ? JSON.parse(stored) : { subjects: [], results: [], uploadedFiles: [] };
  } catch {
    return { subjects: [], results: [], uploadedFiles: [] };
  }
};

export default function Index() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState({ name: '', email: '' });
  const [currentView, setCurrentView] = useState('upload');
  const [appState, setAppState] = useState<AppState>({ subjects: [], results: [], uploadedFiles: [] });
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [newSubjectName, setNewSubjectName] = useState('');
  const [studentName, setStudentName] = useState('');
  const [studentId, setStudentId] = useState('');
  const [passThreshold, setPassThreshold] = useState(35);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFileForEval, setSelectedFileForEval] = useState<UploadedFile | null>(null);
  const [manualMarks, setManualMarks] = useState('');
  const [manualMaxMarks, setManualMaxMarks] = useState('100');
  const [evaluationComments, setEvaluationComments] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const schemeInputRef = useRef<HTMLInputElement>(null);


  // Load data on mount
  useEffect(() => {
    setAppState(loadFromStorage());
  }, []);

  // Save data whenever state changes
  useEffect(() => {
    saveToStorage(appState);
  }, [appState]);

  const handleLogin = (name: string, email: string) => {
    setCurrentUser({ name, email });
    setIsLoggedIn(true);
    toast({
      title: "Welcome!",
      description: `Welcome to EvalAI Pro, ${name}! 🚀`
    });
  };

  const createSubject = () => {
    if (!newSubjectName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a subject name",
        variant: "destructive"
      });
      return;
    }

    if (appState.subjects.some(s => s.name.toLowerCase() === newSubjectName.toLowerCase())) {
      toast({
        title: "Error", 
        description: "Subject already exists",
        variant: "destructive"
      });
      return;
    }

    const newSubject: Subject = {
      id: generateId(),
      name: newSubjectName,
      createdAt: new Date().toISOString()
    };

    setAppState(prev => ({
      ...prev,
      subjects: [...prev.subjects, newSubject]
    }));

    setNewSubjectName('');
    toast({
      title: "Success",
      description: `Subject "${newSubjectName}" created successfully`
    });
  };

  const uploadSchemeOfEvaluation = async (subjectId: string, file: File) => {
    if (file.type !== 'application/pdf') {
      toast({
        title: "Error",
        description: "Please upload a PDF file only",
        variant: "destructive"
      });
      return;
    }

    try {
      const content = await readFileAsText(file);
      
      setAppState(prev => ({
        ...prev,
        subjects: prev.subjects.map(subject => 
          subject.id === subjectId 
            ? {
                ...subject,
                schemeFile: {
                  name: file.name,
                  content: content,
                  uploadedAt: new Date().toISOString()
                }
              }
            : subject
        )
      }));

      toast({
        title: "Success",
        description: "Scheme of evaluation uploaded successfully"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to upload scheme file",
        variant: "destructive"
      });
    }
  };

  const readFileAsText = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    setSelectedFiles(Array.from(files));
  };

  const simulateAIEvaluation = async () => {
    if (!selectedSubject) {
      toast({
        title: "Error",
        description: "Please select a subject",
        variant: "destructive"
      });
      return;
    }

    if (selectedFiles.length === 0) {
      toast({
        title: "Error", 
        description: "Please select files to upload",
        variant: "destructive"
      });
      return;
    }

    setIsEvaluating(true);

    try {
      const subject = appState.subjects.find(s => s.id === selectedSubject);
      if (!subject) throw new Error('Subject not found');

      for (const file of selectedFiles) {
        const content = await readFileAsText(file);
        
        // Simulate AI evaluation with random but realistic results
        const marks = Math.floor(Math.random() * 101);
        const maxMarks = 100;
        const percentage = Math.round((marks / maxMarks) * 100);
        const passed = percentage >= passThreshold;
        
        const resultId = generateId();
        const result: EvaluationResult = {
          id: resultId,
          studentName: studentName || file.name.replace(/\.[^/.]+$/, ''),
          studentId: studentId || `STU${Date.now()}`,
          subject: subject.name,
          fileName: file.name,
          marks,
          maxMarks,
          percentage,
          passed,
          uploadedAt: new Date().toISOString(),
          evaluatedAt: new Date().toISOString(),
          comments: `AI-generated evaluation based on ${subject.schemeFile ? 'uploaded scheme' : 'default criteria'}`
        };

        const uploadedFile: UploadedFile = {
          fileName: file.name,
          content,
          subject: subject.name,
          studentName: result.studentName,
          studentId: result.studentId,
          resultId
        };

        setAppState(prev => ({
          ...prev,
          results: [...prev.results, result],
          uploadedFiles: [...prev.uploadedFiles, uploadedFile]
        }));
      }

      setSelectedFiles([]);
      setStudentName('');
      setStudentId('');
      
      toast({
        title: "Success",
        description: `${selectedFiles.length} file(s) evaluated successfully`
      });

    } catch (error) {
      toast({
        title: "Error",
        description: "Evaluation failed. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsEvaluating(false);
    }
  };

  const saveManualEvaluation = () => {
    if (!selectedFileForEval) return;

    const marks = parseInt(manualMarks) || 0;
    const maxMarks = parseInt(manualMaxMarks) || 100;
    const percentage = Math.round((marks / maxMarks) * 100);
    const passed = percentage >= passThreshold;

    const updatedResult: EvaluationResult = {
      id: selectedFileForEval.resultId,
      studentName: selectedFileForEval.studentName,
      studentId: selectedFileForEval.studentId,
      subject: selectedFileForEval.subject,
      fileName: selectedFileForEval.fileName,
      marks,
      maxMarks,
      percentage,
      passed,
      uploadedAt: new Date().toISOString(),
      evaluatedAt: new Date().toISOString(),
      comments: evaluationComments,
      manuallyEvaluated: true
    };

    setAppState(prev => ({
      ...prev,
      results: prev.results.map(r => 
        r.id === selectedFileForEval.resultId ? updatedResult : r
      )
    }));

    setSelectedFileForEval(null);
    setManualMarks('');
    setManualMaxMarks('100');
    setEvaluationComments('');

    toast({
      title: "Success",
      description: "Manual evaluation saved successfully"
    });
  };

  const filteredResults = appState.results.filter(result =>
    result.studentName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    result.studentId.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getSubjectStats = (subjectName: string) => {
    const subjectResults = appState.results.filter(r => r.subject === subjectName);
    const passed = subjectResults.filter(r => r.passed).length;
    const total = subjectResults.length;
    const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;
    
    return { passed, total, passRate };
  };

  const exportData = () => {
    const dataStr = JSON.stringify(appState, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evalai_export_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    
    toast({
      title: "Success",
      description: "Data exported successfully"
    });
  };

  const clearAllData = () => {
    if (confirm('⚠️ This will permanently delete all your data. Are you sure?')) {
      setAppState({ subjects: [], results: [], uploadedFiles: [] });
      toast({
        title: "Success",
        description: "All data cleared successfully"
      });
    }
  };

  // Show login page if not logged in
  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800 animate-fade-in relative overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 opacity-30">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-400/20 to-blue-400/20 animate-gradient-shift"></div>
      </div>

      {/* Floating Shapes */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-20 h-20 bg-white/10 rounded-full top-20 left-10 animate-float" style={{ animationDelay: '0s' }}></div>
        <div className="absolute w-32 h-32 bg-white/10 rounded-full top-60 right-20 animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute w-16 h-16 bg-white/10 rounded-full bottom-20 left-20 animate-float" style={{ animationDelay: '4s' }}></div>
        <div className="absolute w-24 h-24 bg-white/10 rounded-full top-32 right-32 animate-float" style={{ animationDelay: '1s' }}></div>
        <div className="absolute w-28 h-28 bg-white/5 rounded-full bottom-32 right-10 animate-float" style={{ animationDelay: '3s' }}></div>
      </div>

      <div className="relative z-10 flex">
        {/* Sidebar */}
        <div className="w-80 bg-white/95 backdrop-blur-lg shadow-2xl h-screen overflow-y-auto animate-slide-in-right">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center animate-pulse-glow">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                  EvalAI Pro
                </h1>
                <p className="text-sm text-gray-500">Intelligent Assessment</p>
              </div>
            </div>
          </div>

          <nav className="p-4">
            <div className="space-y-2">
              {[
                { id: 'upload', label: 'Upload Scripts', icon: Upload },
                { id: 'subjects', label: 'Subjects', icon: Book },
                { id: 'analytics', label: 'Analytics', icon: BarChart3 },
                { id: 'search', label: 'Search Results', icon: Search },
                { id: 'manual', label: 'Manual Review', icon: Edit },
                { id: 'settings', label: 'Settings', icon: Settings }
              ].map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setCurrentView(id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 hover-lift relative overflow-hidden ${
                    currentView === id
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg animate-shimmer'
                      : 'text-gray-600 hover:bg-gray-100 hover:shadow-lg'
                  }`}
                >
                  <Icon className={`w-5 h-5 transition-transform duration-300`} />
                  <span className="font-medium relative z-10">{label}</span>
                </button>
              ))}
            </div>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="mb-8 bg-white/95 backdrop-blur-lg rounded-2xl p-6 shadow-xl border border-white/20 hover-lift animate-slide-up">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-3xl font-bold text-gray-800 mb-2">Dashboard</h2>
                  <p className="text-gray-600">Manage your assessments with AI-powered intelligence</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center text-white font-bold animate-pulse-glow">
                    {currentUser.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-800">{currentUser.name}</div>
                    <div className="text-sm text-gray-500">{currentUser.email}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Upload View */}
            {currentView === 'upload' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20 animate-slide-up hover-lift">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="w-6 h-6 text-purple-600" />
                    Upload Answer Scripts
                  </CardTitle>
                  <CardDescription>
                    Upload student answer scripts for AI-powered evaluation
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="subject-select">Subject</Label>
                      <Select value={selectedSubject} onValueChange={setSelectedSubject}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a subject" />
                        </SelectTrigger>
                        <SelectContent>
                          {appState.subjects.map(subject => (
                            <SelectItem key={subject.id} value={subject.id}>
                              {subject.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="new-subject">New Subject</Label>
                      <Input
                        id="new-subject"
                        value={newSubjectName}
                        onChange={(e) => setNewSubjectName(e.target.value)}
                        placeholder="Enter subject name"
                      />
                    </div>
                    <div className="flex items-end">
                      <Button onClick={createSubject} className="w-full bg-gradient-to-r from-purple-600 to-blue-600">
                        <Plus className="w-4 h-4 mr-2" />
                        Create Subject
                      </Button>
                    </div>
                  </div>

                  {/* File Upload Zone */}
                  <div
                    className="border-2 border-dashed border-purple-300 rounded-xl p-12 text-center bg-gradient-to-br from-purple-50 to-blue-50 hover:border-purple-400 transition-all duration-300 cursor-pointer hover-lift animate-shimmer relative overflow-hidden"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                    <div className="text-lg font-semibold text-gray-700 mb-2 relative z-10">
                      Drag & drop your files here
                    </div>
                    <div className="text-gray-500 relative z-10">
                      or click to browse and select files
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      onChange={(e) => handleFileSelect(e.target.files)}
                      className="hidden"
                    />
                  </div>

                  {/* Selected Files */}
                  {selectedFiles.length > 0 && (
                    <div className="space-y-2">
                      <Label>Selected Files ({selectedFiles.length})</Label>
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {selectedFiles.map((file, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover-lift animate-slide-in-right" style={{ animationDelay: `${index * 0.1}s` }}>
                            <div className="flex items-center gap-3">
                              <FileText className="w-5 h-5 text-blue-500 animate-pulse" />
                              <div>
                                <div className="font-medium">{file.name}</div>
                                <div className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</div>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setSelectedFiles(files => files.filter((_, i) => i !== index))}
                              className="hover:bg-red-50 hover:text-red-600 transition-colors duration-300"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label htmlFor="student-name">Student Name (Optional)</Label>
                      <Input
                        id="student-name"
                        value={studentName}
                        onChange={(e) => setStudentName(e.target.value)}
                        placeholder="Enter student name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="student-id">Student ID (Optional)</Label>
                      <Input
                        id="student-id"
                        value={studentId}
                        onChange={(e) => setStudentId(e.target.value)}
                        placeholder="Enter student ID"
                      />
                    </div>
                    <div>
                      <Label htmlFor="pass-threshold">Pass Threshold (%)</Label>
                      <Input
                        id="pass-threshold"
                        type="number"
                        min="0"
                        max="100"
                        value={passThreshold}
                        onChange={(e) => setPassThreshold(parseInt(e.target.value) || 35)}
                      />
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <Button 
                      onClick={simulateAIEvaluation}
                      disabled={isEvaluating}
                      className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600"
                    >
                      {isEvaluating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <Brain className="w-4 h-4 mr-2" />
                          AI Auto-Evaluate
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Subjects View */}
            {currentView === 'subjects' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Book className="w-6 h-6 text-purple-600" />
                    Subject Management
                  </CardTitle>
                  <CardDescription>
                    View and manage all your subjects with their evaluation schemes and statistics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appState.subjects.length === 0 ? (
                    <div className="text-center py-12">
                      <Book className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">No subjects yet</h3>
                      <p className="text-gray-500 mb-4">Create your first subject to get started with evaluations.</p>
                      <Button 
                        onClick={() => setCurrentView('upload')}
                        className="bg-gradient-to-r from-purple-600 to-blue-600"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Create Subject
                      </Button>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {appState.subjects.map(subject => {
                        const stats = getSubjectStats(subject.name);
                        return (
                          <Card key={subject.id} className="relative overflow-hidden border-2 hover:border-purple-300 transition-colors">
                            <CardHeader>
                              <div className="flex justify-between items-start">
                                <div>
                                  <CardTitle className="flex items-center gap-2">
                                    <Book className="w-5 h-5 text-purple-600" />
                                    {subject.name}
                                  </CardTitle>
                                  <CardDescription>
                                    {stats.total} submission{stats.total !== 1 ? 's' : ''}
                                  </CardDescription>
                                </div>
                                <div className="text-right">
                                  <div className={`text-2xl font-bold ${
                                    stats.passRate >= 70 ? 'text-green-600' : 
                                    stats.passRate >= 50 ? 'text-yellow-600' : 'text-red-600'
                                  }`}>
                                    {stats.passRate}%
                                  </div>
                                  <div className="text-sm text-gray-500">Pass Rate</div>
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              {/* Scheme of Evaluation Section */}
                              <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200">
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-2">
                                    <FileUp className="w-4 h-4 text-purple-600" />
                                    <span className="font-medium text-gray-700">Evaluation Scheme</span>
                                  </div>
                                  {subject.schemeFile && (
                                    <Badge variant="secondary" className="bg-green-100 text-green-700">
                                      <Check className="w-3 h-3 mr-1" />
                                      Uploaded
                                    </Badge>
                                  )}
                                </div>
                                
                                {subject.schemeFile ? (
                                  <div className="space-y-2">
                                    <div className="flex items-center gap-2 text-sm text-gray-600">
                                      <FileText className="w-4 h-4" />
                                      <span className="font-medium">{subject.schemeFile.name}</span>
                                    </div>
                                    <div className="text-xs text-gray-500">
                                      Uploaded on {new Date(subject.schemeFile.uploadedAt).toLocaleDateString()}
                                    </div>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => schemeInputRef.current?.click()}
                                      className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                                    >
                                      <Upload className="w-3 h-3 mr-1" />
                                      Update Scheme
                                    </Button>
                                  </div>
                                ) : (
                                  <div className="space-y-2">
                                    <p className="text-sm text-gray-600">
                                      Upload a PDF scheme that defines how marks should be allocated for each question and answer evaluation criteria.
                                    </p>
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => schemeInputRef.current?.click()}
                                      className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                                    >
                                      <FileUp className="w-3 h-3 mr-1" />
                                      Upload Scheme (PDF)
                                    </Button>
                                  </div>
                                )}
                                
                                <input
                                  ref={schemeInputRef}
                                  type="file"
                                  accept=".pdf"
                                  onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) {
                                      uploadSchemeOfEvaluation(subject.id, file);
                                    }
                                  }}
                                  className="hidden"
                                />
                              </div>

                              {/* Statistics */}
                              <div className="grid grid-cols-2 gap-3">
                                <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
                                  <div className="text-xl font-bold text-green-600">{stats.passed}</div>
                                  <div className="text-sm text-green-700">Passed</div>
                                </div>
                                <div className="text-center p-3 bg-red-50 rounded-lg border border-red-200">
                                  <div className="text-xl font-bold text-red-600">{stats.total - stats.passed}</div>
                                  <div className="text-sm text-red-700">Failed</div>
                                </div>
                              </div>

                              {stats.total > 0 && (
                                <div>
                                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                                    <span>Progress</span>
                                    <span>{stats.passed}/{stats.total}</span>
                                  </div>
                                  <Progress value={stats.passRate} className="h-2" />
                                </div>
                              )}

                              <Button
                                variant="ghost"
                                className="w-full text-purple-600 hover:bg-purple-50"
                                onClick={() => {
                                  setCurrentView('analytics');
                                  // Focus on this subject in analytics
                                }}
                              >
                                <BarChart3 className="w-4 h-4 mr-2" />
                                View Analytics
                              </Button>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Analytics View */}
            {currentView === 'analytics' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="w-6 h-6 text-purple-600" />
                    Analytics & Reports
                  </CardTitle>
                  <CardDescription>
                    View detailed analytics and performance metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appState.results.length === 0 ? (
                    <div className="text-center py-12">
                      <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">No data yet</h3>
                      <p className="text-gray-500">Upload and evaluate some files to see analytics.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* Overview Stats */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-blue-600">{appState.results.length}</div>
                            <div className="text-sm text-blue-700">Total Evaluations</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-green-600">
                              {appState.results.filter(r => r.passed).length}
                            </div>
                            <div className="text-sm text-green-700">Passed</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-red-600">
                              {appState.results.filter(r => !r.passed).length}
                            </div>
                            <div className="text-sm text-red-700">Failed</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-purple-600">
                              {Math.round((appState.results.filter(r => r.passed).length / appState.results.length) * 100)}%
                            </div>
                            <div className="text-sm text-purple-700">Pass Rate</div>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Subject-wise breakdown */}
                      <Card>
                        <CardHeader>
                          <CardTitle>Subject Performance</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-4">
                            {appState.subjects.map(subject => {
                              const stats = getSubjectStats(subject.name);
                              return (
                                <div key={subject.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                  <div className="flex items-center gap-3">
                                    <Book className="w-5 h-5 text-purple-600" />
                                    <div>
                                      <div className="font-medium">{subject.name}</div>
                                      <div className="text-sm text-gray-500">
                                        {stats.total} submission{stats.total !== 1 ? 's' : ''}
                                        {subject.schemeFile && (
                                          <Badge variant="secondary" className="ml-2 bg-green-100 text-green-700">
                                            <FileText className="w-3 h-3 mr-1" />
                                            Scheme Uploaded
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-4">
                                    <div className="text-right">
                                      <div className={`text-lg font-bold ${
                                        stats.passRate >= 70 ? 'text-green-600' : 
                                        stats.passRate >= 50 ? 'text-yellow-600' : 'text-red-600'
                                      }`}>
                                        {stats.passRate}%
                                      </div>
                                      <div className="text-sm text-gray-500">{stats.passed}/{stats.total}</div>
                                    </div>
                                    <div className="w-24">
                                      <Progress value={stats.passRate} className="h-2" />
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Search View */}
            {currentView === 'search' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Search className="w-6 h-6 text-purple-600" />
                    Search Results
                  </CardTitle>
                  <CardDescription>
                    Search for specific students or results
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex gap-4">
                    <Input
                      placeholder="Search by student name or ID..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="flex-1"
                    />
                    <Button className="bg-gradient-to-r from-purple-600 to-blue-600">
                      <Search className="w-4 h-4 mr-2" />
                      Search
                    </Button>
                  </div>

                  {searchQuery && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">
                        Search Results ({filteredResults.length} found)
                      </h3>
                      
                      {filteredResults.length === 0 ? (
                        <div className="text-center py-8">
                          <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                          <p className="text-gray-500">No results found for "{searchQuery}"</p>
                        </div>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Student</TableHead>
                              <TableHead>ID</TableHead>
                              <TableHead>Subject</TableHead>
                              <TableHead>Score</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Type</TableHead>
                              <TableHead>Date</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {filteredResults.map(result => (
                              <TableRow key={result.id}>
                                <TableCell className="font-medium">{result.studentName}</TableCell>
                                <TableCell>{result.studentId}</TableCell>
                                <TableCell>
                                  <Badge variant="secondary">{result.subject}</Badge>
                                </TableCell>
                                <TableCell>
                                  <div className="flex items-center gap-2">
                                    <span>{result.marks}/{result.maxMarks}</span>
                                    <span className="text-gray-500">({result.percentage}%)</span>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <Badge variant={result.passed ? "default" : "destructive"}>
                                    {result.passed ? "Pass" : "Fail"}
                                  </Badge>
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline">
                                    {result.manuallyEvaluated ? "Manual" : "AI"}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-gray-500">
                                  {new Date(result.evaluatedAt).toLocaleDateString()}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Manual Review */}
            {currentView === 'manual' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Edit className="w-6 h-6 text-purple-600" />
                    Manual Review & Evaluation
                  </CardTitle>
                  <CardDescription>
                    Review and manually evaluate uploaded files
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Select Subject</Label>
                      <Select value={selectedSubject} onValueChange={setSelectedSubject}>
                        <SelectTrigger>
                          <SelectValue placeholder="Choose a subject" />
                        </SelectTrigger>
                        <SelectContent>
                          {appState.subjects.map(subject => (
                            <SelectItem key={subject.id} value={subject.name}>
                              {subject.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {selectedSubject && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">
                        Files for Manual Review - {selectedSubject}
                      </h3>
                      
                      {appState.uploadedFiles.filter(f => f.subject === selectedSubject).length === 0 ? (
                        <div className="text-center py-8">
                          <Edit className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                          <p className="text-gray-500">No files found for this subject</p>
                        </div>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>File Name</TableHead>
                              <TableHead>Student</TableHead>
                              <TableHead>Current Status</TableHead>
                              <TableHead>Action</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {appState.uploadedFiles
                              .filter(f => f.subject === selectedSubject)
                              .map(file => {
                                const result = appState.results.find(r => r.id === file.resultId);
                                return (
                                  <TableRow key={file.resultId}>
                                    <TableCell>
                                      <div className="flex items-center gap-2">
                                        <FileText className="w-4 h-4 text-blue-500" />
                                        {file.fileName}
                                      </div>
                                    </TableCell>
                                    <TableCell>{file.studentName}</TableCell>
                                    <TableCell>
                                      {result ? (
                                        <div className="flex items-center gap-2">
                                          <span>{result.marks}/{result.maxMarks} ({result.percentage}%)</span>
                                          <Badge variant={result.passed ? "default" : "destructive"}>
                                            {result.passed ? "Pass" : "Fail"}
                                          </Badge>
                                          {result.manuallyEvaluated && (
                                            <Badge variant="outline">Manual</Badge>
                                          )}
                                        </div>
                                      ) : (
                                        <span className="text-gray-500">Not evaluated</span>
                                      )}
                                    </TableCell>
                                    <TableCell>
                                      <Dialog>
                                        <DialogTrigger asChild>
                                          <Button 
                                            variant="ghost" 
                                            size="sm"
                                            onClick={() => {
                                              setSelectedFileForEval(file);
                                              if (result) {
                                                setManualMarks(result.marks.toString());
                                                setManualMaxMarks(result.maxMarks.toString());
                                                setEvaluationComments(result.comments || '');
                                              }
                                            }}
                                          >
                                            <Eye className="w-4 h-4 mr-2" />
                                            Review
                                          </Button>
                                        </DialogTrigger>
                                        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                                          <DialogHeader>
                                            <DialogTitle>Manual Evaluation - {file.fileName}</DialogTitle>
                                            <DialogDescription>
                                              Review the file content and provide manual evaluation
                                            </DialogDescription>
                                          </DialogHeader>
                                          
                                          <div className="space-y-6">
                                            <div>
                                              <Label>File Content</Label>
                                              <div className="mt-2 p-4 bg-gray-50 rounded-lg max-h-60 overflow-y-auto border">
                                                <pre className="text-sm whitespace-pre-wrap font-mono">
                                                  {file.content}
                                                </pre>
                                              </div>
                                            </div>

                                            <div className="grid grid-cols-2 gap-4">
                                              <div>
                                                <Label htmlFor="manual-marks">Marks Obtained</Label>
                                                <Input
                                                  id="manual-marks"
                                                  type="number"
                                                  min="0"
                                                  value={manualMarks}
                                                  onChange={(e) => setManualMarks(e.target.value)}
                                                  placeholder="Enter marks"
                                                />
                                              </div>
                                              <div>
                                                <Label htmlFor="manual-max-marks">Maximum Marks</Label>
                                                <Input
                                                  id="manual-max-marks"
                                                  type="number"
                                                  min="1"
                                                  value={manualMaxMarks}
                                                  onChange={(e) => setManualMaxMarks(e.target.value)}
                                                />
                                              </div>
                                            </div>

                                            <div>
                                              <Label htmlFor="evaluation-comments">Evaluation Comments</Label>
                                              <Textarea
                                                id="evaluation-comments"
                                                value={evaluationComments}
                                                onChange={(e) => setEvaluationComments(e.target.value)}
                                                placeholder="Add detailed feedback and comments..."
                                                className="h-24"
                                              />
                                            </div>

                                            <div className="flex gap-4">
                                              <Button 
                                                onClick={() => {
                                                  saveManualEvaluation();
                                                  // Close dialog by resetting form
                                                  setSelectedFileForEval(null);
                                                  setManualMarks('');
                                                  setManualMaxMarks('100');
                                                  setEvaluationComments('');
                                                }}
                                                className="bg-gradient-to-r from-green-500 to-blue-500"
                                              >
                                                <Save className="w-4 h-4 mr-2" />
                                                Save Evaluation
                                              </Button>
                                            </div>
                                          </div>
                                        </DialogContent>
                                      </Dialog>
                                    </TableCell>
                                  </TableRow>
                                );
                              })}
                          </TableBody>
                        </Table>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Settings View */}
            {currentView === 'settings' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="w-6 h-6 text-purple-600" />
                    Settings & Data Management
                  </CardTitle>
                  <CardDescription>
                    Manage your data, export reports, and configure system settings
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Button onClick={exportData} className="bg-gradient-to-r from-blue-500 to-purple-500">
                      <Download className="w-4 h-4 mr-2" />
                      Export Data
                    </Button>
                    <Button variant="outline">
                      <Upload className="w-4 h-4 mr-2" />
                      Import Data
                    </Button>
                    <Button variant="destructive" onClick={clearAllData}>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Clear All Data
                    </Button>
                  </div>

                  <Card className="bg-blue-50 border-blue-200">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                          <div className="w-3 h-3 bg-white rounded-full" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-blue-900 mb-2">Data Storage Information</h4>
                          <p className="text-blue-800 text-sm leading-relaxed">
                            All data in this demo is stored locally in your browser. Your information is private and secure, 
                            never transmitted to external servers. Use the export feature to backup your data.
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Storage Statistics</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Subjects:</span>
                          <span className="font-semibold">{appState.subjects.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Total Evaluations:</span>
                          <span className="font-semibold">{appState.results.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Uploaded Files:</span>
                          <span className="font-semibold">{appState.uploadedFiles.length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Schemes Uploaded:</span>
                          <span className="font-semibold">
                            {appState.subjects.filter(s => s.schemeFile).length}
                          </span>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Performance Overview</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Total Passed:</span>
                          <span className="font-semibold text-green-600">
                            {appState.results.filter(r => r.passed).length}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Total Failed:</span>
                          <span className="font-semibold text-red-600">
                            {appState.results.filter(r => !r.passed).length}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Overall Pass Rate:</span>
                          <span className="font-semibold text-purple-600">
                            {appState.results.length > 0 
                              ? Math.round((appState.results.filter(r => r.passed).length / appState.results.length) * 100)
                              : 0}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Manual Evaluations:</span>
                          <span className="font-semibold">
                            {appState.results.filter(r => r.manuallyEvaluated).length}
                          </span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

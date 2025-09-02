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
import LoginReal from "./LoginReal";
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
  Download,
  LogOut,
  Loader2
} from "lucide-react";

// Import API services
import api, { 
  type User, 
  type EvaluationScheme, 
  type ExamSession,
  type EvaluationResult,
  authApi,
  schemesApi,
  sessionsApi,
  scriptsApi,
  evaluationsApi
} from "../services/api";

// Updated interfaces to match backend
interface AppState {
  user: User | null;
  schemes: EvaluationScheme[];
  sessions: ExamSession[];
  currentSession: ExamSession | null;
  sessionResults: EvaluationResult[];
  reviewQueue: any[];
}

export default function IndexReal() {
  // Auth state
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  
  // App state
  const [appState, setAppState] = useState<AppState>({
    user: null,
    schemes: [],
    sessions: [],
    currentSession: null,
    sessionResults: [],
    reviewQueue: []
  });
  
  // UI state
  const [currentView, setCurrentView] = useState('upload');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedScheme, setSelectedScheme] = useState('');
  const [selectedSession, setSelectedSession] = useState('');
  const [newSessionName, setNewSessionName] = useState('');
  
  // New scheme form
  const [newSchemeName, setNewSchemeName] = useState('');
  const [newSchemeSubject, setNewSchemeSubject] = useState('');
  const [newSchemeTotalMarks, setNewSchemeTotalMarks] = useState(100);
  const [newSchemePassingMarks, setNewSchemePassingMarks] = useState(40);
  
  // Student info
  const [studentName, setStudentName] = useState('');
  const [studentId, setStudentId] = useState('');
  
  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [uploadProgress, setUploadProgress] = useState<{[key: string]: number}>({});
  
  // Search
  const [searchQuery, setSearchQuery] = useState('');
  
  // Manual review
  const [selectedReview, setSelectedReview] = useState<any>(null);
  const [manualScore, setManualScore] = useState('');
  const [reviewNotes, setReviewNotes] = useState('');
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const schemeFileRef = useRef<HTMLInputElement>(null);

  // Check authentication on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  // Load data when user logs in
  useEffect(() => {
    if (isLoggedIn && appState.user) {
      loadInitialData();
    }
  }, [isLoggedIn, appState.user]);

  const checkAuthStatus = async () => {
    try {
      if (authApi.isAuthenticated()) {
        const user = await authApi.getCurrentUser();
        setAppState(prev => ({ ...prev, user }));
        setIsLoggedIn(true);
      }
    } catch (error) {
      authApi.logout();
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = (user: User) => {
    setAppState(prev => ({ ...prev, user }));
    setIsLoggedIn(true);
    toast({
      title: "Welcome!",
      description: `Welcome to EvalAI Pro, ${user.full_name}! 🚀`
    });
  };

  const handleLogout = () => {
    authApi.logout();
    setIsLoggedIn(false);
    setAppState({
      user: null,
      schemes: [],
      sessions: [],
      currentSession: null,
      sessionResults: [],
      reviewQueue: []
    });
    toast({
      title: "Logged Out",
      description: "You have been logged out successfully."
    });
  };

  const loadInitialData = async () => {
    try {
      // Load schemes
      const schemes = await schemesApi.list();
      setAppState(prev => ({ ...prev, schemes }));

      // Load sessions
      const sessions = await sessionsApi.list();
      setAppState(prev => ({ ...prev, sessions }));

      // Load review queue
      const reviewData = await evaluationsApi.getReviewQueue();
      setAppState(prev => ({ ...prev, reviewQueue: reviewData.reviews }));

    } catch (error) {
      console.error('Failed to load initial data:', error);
      toast({
        title: "Loading Error",
        description: "Failed to load some data. Please refresh the page.",
        variant: "destructive"
      });
    }
  };

  const createScheme = async () => {
    if (!newSchemeName.trim() || !newSchemeSubject.trim()) {
      toast({
        title: "Error",
        description: "Please enter scheme name and subject",
        variant: "destructive"
      });
      return;
    }

    try {
      // Create a basic scheme - in real app, you'd have a more detailed form
      const newScheme = await schemesApi.create({
        scheme_name: newSchemeName,
        subject: newSchemeSubject,
        total_marks: newSchemeTotalMarks,
        passing_marks: newSchemePassingMarks,
        questions: [
          {
            question_number: 1,
            max_marks: newSchemeTotalMarks,
            concepts: [
              {
                concept: "General understanding and accuracy",
                keywords: ["correct", "accurate", "complete", "clear"],
                weight: 1.0,
                marks_allocation: newSchemeTotalMarks
              }
            ]
          }
        ]
      });

      setAppState(prev => ({
        ...prev,
        schemes: [...prev.schemes, newScheme]
      }));

      setNewSchemeName('');
      setNewSchemeSubject('');
      setNewSchemeTotalMarks(100);
      setNewSchemePassingMarks(40);

      toast({
        title: "Success",
        description: `Scheme "${newSchemeName}" created successfully`
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create scheme",
        variant: "destructive"
      });
    }
  };

  const createSession = async () => {
    if (!newSessionName.trim() || !selectedScheme) {
      toast({
        title: "Error",
        description: "Please enter session name and select a scheme",
        variant: "destructive"
      });
      return;
    }

    try {
      const session = await sessionsApi.create({
        session_name: newSessionName,
        scheme_id: selectedScheme
      });

      setAppState(prev => ({
        ...prev,
        sessions: [...prev.sessions, session],
        currentSession: session
      }));

      setNewSessionName('');
      setSelectedSession(session.id);

      toast({
        title: "Success",
        description: `Session "${newSessionName}" created successfully`
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to create session",
        variant: "destructive"
      });
    }
  };

  const handleFileSelect = (files: FileList | null) => {
    if (!files) return;
    
    const fileArray = Array.from(files);
    
    // Validate files
    const validFiles = fileArray.filter(file => {
      if (!file.type.startsWith('image/')) {
        toast({
          title: "Invalid File",
          description: `${file.name} is not an image file`,
          variant: "destructive"
        });
        return false;
      }
      
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        toast({
          title: "File Too Large", 
          description: `${file.name} is larger than 10MB`,
          variant: "destructive"
        });
        return false;
      }
      
      return true;
    });
    
    setSelectedFiles(validFiles);
  };

  const uploadAndProcessFiles = async () => {
    if (!selectedSession) {
      toast({
        title: "Error",
        description: "Please select a session first",
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

    setIsProcessing(true);
    setProcessingProgress(0);

    try {
      // Upload files
      const uploadResult = await scriptsApi.uploadBatch(selectedSession, selectedFiles);
      
      setProcessingProgress(50);

      toast({
        title: "Upload Successful",
        description: `${uploadResult.uploaded_count} files uploaded. ${uploadResult.processing_mode === 'real_time' ? 'Processing now...' : 'Queued for processing...'}`
      });

      // If real-time processing, wait a bit and refresh results
      if (uploadResult.processing_mode === 'real_time') {
        setTimeout(() => {
          loadSessionResults();
          setProcessingProgress(100);
        }, 2000);
      } else {
        setProcessingProgress(100);
      }

      // Clear selected files
      setSelectedFiles([]);

      // Show errors if any
      if (uploadResult.errors.length > 0) {
        uploadResult.errors.forEach(error => {
          toast({
            title: "File Error",
            description: error,
            variant: "destructive"
          });
        });
      }

    } catch (error) {
      toast({
        title: "Upload Failed",
        description: error instanceof Error ? error.message : "Failed to upload files",
        variant: "destructive"
      });
    } finally {
      setIsProcessing(false);
      setProcessingProgress(0);
    }
  };

  const loadSessionResults = async () => {
    if (!selectedSession) return;

    try {
      const results = await evaluationsApi.getSessionResults(selectedSession);
      setAppState(prev => ({
        ...prev,
        sessionResults: results.results
      }));
    } catch (error) {
      console.error('Failed to load session results:', error);
    }
  };

  const uploadSchemeFile = async (schemeId: string, file: File) => {
    try {
      await schemesApi.uploadFile(schemeId, file);
      
      // Refresh schemes
      const schemes = await schemesApi.list();
      setAppState(prev => ({ ...prev, schemes }));

      toast({
        title: "Success",
        description: "Scheme file uploaded successfully"
      });
    } catch (error) {
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to upload scheme file",
        variant: "destructive"
      });
    }
  };

  const filteredResults = appState.sessionResults.filter(result =>
    result.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    result.student_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getSchemeStats = (schemeId: string) => {
    const schemeResults = appState.sessionResults.filter(r => 
      appState.sessions.find(s => s.id === selectedSession)?.scheme_id === schemeId
    );
    const passed = schemeResults.filter(r => r.passed).length;
    const total = schemeResults.length;
    const passRate = total > 0 ? Math.round((passed / total) * 100) : 0;
    
    return { passed, total, passRate };
  };

  // Show loading screen during initial auth check
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800">
        <div className="text-center">
          <Loader2 className="w-16 h-16 text-white animate-spin mx-auto mb-4" />
          <p className="text-white text-lg">Loading EvalAI Pro...</p>
        </div>
      </div>
    );
  }

  // Show login page if not logged in
  if (!isLoggedIn) {
    return <LoginReal onLogin={handleLogin} />;
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
                { id: 'schemes', label: 'Schemes', icon: Book },
                { id: 'sessions', label: 'Sessions', icon: FileText },
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
                  <Button
                    variant="outline"
                    onClick={handleLogout}
                    className="flex items-center gap-2"
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </Button>
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center text-white font-bold animate-pulse-glow">
                    {appState.user?.full_name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-800">{appState.user?.full_name}</div>
                    <div className="text-sm text-gray-500">{appState.user?.email}</div>
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
                  {/* Scheme and Session Selection */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="scheme-select">Evaluation Scheme</Label>
                      <Select value={selectedScheme} onValueChange={setSelectedScheme}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a scheme" />
                        </SelectTrigger>
                        <SelectContent>
                          {appState.schemes.map(scheme => (
                            <SelectItem key={scheme.id} value={scheme.id}>
                              {scheme.scheme_name} - {scheme.subject}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label htmlFor="session-select">Exam Session</Label>
                      <Select value={selectedSession} onValueChange={setSelectedSession}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select or create session" />
                        </SelectTrigger>
                        <SelectContent>
                          {appState.sessions
                            .filter(session => !selectedScheme || session.scheme_id === selectedScheme)
                            .map(session => (
                            <SelectItem key={session.id} value={session.id}>
                              {session.session_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Create New Session */}
                  {selectedScheme && (
                    <div className="p-4 bg-gray-50 rounded-lg border">
                      <Label htmlFor="new-session">Create New Session</Label>
                      <div className="flex gap-2 mt-2">
                        <Input
                          id="new-session"
                          value={newSessionName}
                          onChange={(e) => setNewSessionName(e.target.value)}
                          placeholder="Enter session name (e.g., Mid-term March 2025)"
                          className="flex-1"
                        />
                        <Button onClick={createSession} disabled={!newSessionName.trim()}>
                          <Plus className="w-4 h-4 mr-2" />
                          Create
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* File Upload Zone */}
                  <div
                    className="border-2 border-dashed border-purple-300 rounded-xl p-12 text-center bg-gradient-to-br from-purple-50 to-blue-50 hover:border-purple-400 transition-all duration-300 cursor-pointer hover-lift animate-shimmer relative overflow-hidden"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload className="w-16 h-16 text-purple-400 mx-auto mb-4" />
                    <div className="text-lg font-semibold text-gray-700 mb-2 relative z-10">
                      Drag & drop your answer sheets here
                    </div>
                    <div className="text-gray-500 relative z-10">
                      or click to browse and select image files (JPG, PNG, etc.)
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept="image/*"
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
                                <div className="text-sm text-gray-500">{(file.size / 1024 / 1024).toFixed(1)} MB</div>
                              </div>
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedFiles(files => files.filter((_, i) => i !== index));
                              }}
                              className="hover:bg-red-50 hover:text-red-600 transition-colors duration-300"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Processing Progress */}
                  {isProcessing && (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin text-purple-600" />
                        <span className="font-medium">Processing files...</span>
                      </div>
                      <Progress value={processingProgress} className="h-2" />
                      <p className="text-sm text-gray-600">
                        Uploading files and running AI evaluation. This may take a few minutes.
                      </p>
                    </div>
                  )}

                  {/* Upload Button */}
                  <div className="flex gap-4">
                    <Button 
                      onClick={uploadAndProcessFiles}
                      disabled={isProcessing || !selectedSession || selectedFiles.length === 0}
                      className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600"
                    >
                      {isProcessing ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <Brain className="w-4 h-4 mr-2" />
                          Upload & Evaluate
                        </>
                      )}
                    </Button>

                    {selectedSession && (
                      <Button 
                        variant="outline"
                        onClick={loadSessionResults}
                        className="border-purple-300 text-purple-700 hover:bg-purple-50"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        View Results
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Schemes View */}
            {currentView === 'schemes' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Book className="w-6 h-6 text-purple-600" />
                    Evaluation Schemes
                  </CardTitle>
                  <CardDescription>
                    Create and manage evaluation schemes for different subjects
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Create New Scheme */}
                  <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg">
                    <h3 className="text-lg font-semibold mb-4">Create New Scheme</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="scheme-name">Scheme Name</Label>
                        <Input
                          id="scheme-name"
                          value={newSchemeName}
                          onChange={(e) => setNewSchemeName(e.target.value)}
                          placeholder="e.g., Data Structures Mid-term"
                        />
                      </div>
                      <div>
                        <Label htmlFor="scheme-subject">Subject</Label>
                        <Input
                          id="scheme-subject"
                          value={newSchemeSubject}
                          onChange={(e) => setNewSchemeSubject(e.target.value)}
                          placeholder="e.g., Computer Science"
                        />
                      </div>
                      <div>
                        <Label htmlFor="total-marks">Total Marks</Label>
                        <Input
                          id="total-marks"
                          type="number"
                          value={newSchemeTotalMarks}
                          onChange={(e) => setNewSchemeTotalMarks(parseInt(e.target.value) || 100)}
                          min="1"
                        />
                      </div>
                      <div>
                        <Label htmlFor="passing-marks">Passing Marks</Label>
                        <Input
                          id="passing-marks"
                          type="number"
                          value={newSchemePassingMarks}
                          onChange={(e) => setNewSchemePassingMarks(parseInt(e.target.value) || 40)}
                          min="1"
                          max={newSchemeTotalMarks}
                        />
                      </div>
                    </div>
                    <Button onClick={createScheme} className="mt-4 bg-gradient-to-r from-purple-600 to-blue-600">
                      <Plus className="w-4 h-4 mr-2" />
                      Create Scheme
                    </Button>
                  </div>

                  {/* Existing Schemes */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {appState.schemes.map(scheme => (
                      <Card key={scheme.id} className="border-2 hover:border-purple-300 transition-colors">
                        <CardHeader>
                          <div className="flex justify-between items-start">
                            <div>
                              <CardTitle className="flex items-center gap-2 text-lg">
                                <Book className="w-5 h-5 text-purple-600" />
                                {scheme.scheme_name}
                              </CardTitle>
                              <CardDescription>{scheme.subject}</CardDescription>
                            </div>
                            <Badge variant="outline">
                              {scheme.total_marks} marks
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <div className="flex justify-between text-sm">
                              <span>Passing Marks:</span>
                              <span className="font-medium">{scheme.passing_marks}/{scheme.total_marks}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span>Questions:</span>
                              <span className="font-medium">{scheme.questions.length}</span>
                            </div>
                            
                            {/* Scheme File Upload */}
                            <div className="pt-3 border-t">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium">Scheme File</span>
                                {scheme.scheme_file && (
                                  <Badge variant="secondary" className="bg-green-100 text-green-700">
                                    <Check className="w-3 h-3 mr-1" />
                                    Uploaded
                                  </Badge>
                                )}
                              </div>
                              
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  const input = document.createElement('input');
                                  input.type = 'file';
                                  input.accept = '.pdf';
                                  input.onchange = (e) => {
                                    const file = (e.target as HTMLInputElement).files?.[0];
                                    if (file) {
                                      uploadSchemeFile(scheme.id, file);
                                    }
                                  };
                                  input.click();
                                }}
                                className="w-full"
                              >
                                <FileUp className="w-3 h-3 mr-1" />
                                {scheme.scheme_file ? 'Update File' : 'Upload PDF'}
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {appState.schemes.length === 0 && (
                    <div className="text-center py-12">
                      <Book className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">No schemes yet</h3>
                      <p className="text-gray-500">Create your first evaluation scheme to get started.</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Sessions View */}
            {currentView === 'sessions' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="w-6 h-6 text-purple-600" />
                    Exam Sessions
                  </CardTitle>
                  <CardDescription>
                    View and manage your exam sessions
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {appState.sessions.map(session => {
                      const scheme = appState.schemes.find(s => s.id === session.scheme_id);
                      return (
                        <Card key={session.id} className="border-2 hover:border-purple-300 transition-colors">
                          <CardHeader>
                            <CardTitle className="text-lg">{session.session_name}</CardTitle>
                            <CardDescription>
                              {scheme ? `${scheme.scheme_name} - ${scheme.subject}` : 'Unknown Scheme'}
                            </CardDescription>
                          </CardHeader>
                          <CardContent>
                            <div className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span>Status:</span>
                                <Badge variant={
                                  session.status === 'completed' ? 'default' :
                                  session.status === 'processing' ? 'secondary' :
                                  session.status === 'failed' ? 'destructive' : 'outline'
                                }>
                                  {session.status}
                                </Badge>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span>Students:</span>
                                <span>{session.processed_count}/{session.total_students}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span>Created:</span>
                                <span>{new Date(session.created_at).toLocaleDateString()}</span>
                              </div>
                              
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setSelectedSession(session.id);
                                  setCurrentView('analytics');
                                  loadSessionResults();
                                }}
                                className="w-full mt-3"
                              >
                                <BarChart3 className="w-4 h-4 mr-2" />
                                View Results
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>

                  {appState.sessions.length === 0 && (
                    <div className="text-center py-12">
                      <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">No sessions yet</h3>
                      <p className="text-gray-500">Create your first exam session to start evaluating answer sheets.</p>
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
                    Analytics & Results
                  </CardTitle>
                  <CardDescription>
                    View evaluation results and performance metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedSession && appState.sessionResults.length > 0 ? (
                    <div className="space-y-6">
                      {/* Overview Stats */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-blue-600">{appState.sessionResults.length}</div>
                            <div className="text-sm text-blue-700">Total Evaluated</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-green-600">
                              {appState.sessionResults.filter(r => r.passed).length}
                            </div>
                            <div className="text-sm text-green-700">Passed</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-red-600">
                              {appState.sessionResults.filter(r => !r.passed).length}
                            </div>
                            <div className="text-sm text-red-700">Failed</div>
                          </CardContent>
                        </Card>
                        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                          <CardContent className="p-4 text-center">
                            <div className="text-2xl font-bold text-purple-600">
                              {Math.round((appState.sessionResults.filter(r => r.passed).length / appState.sessionResults.length) * 100)}%
                            </div>
                            <div className="text-sm text-purple-700">Pass Rate</div>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Results Table */}
                      <Card>
                        <CardHeader>
                          <CardTitle>Evaluation Results</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Student</TableHead>
                                <TableHead>ID</TableHead>
                                <TableHead>Score</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Review</TableHead>
                                <TableHead>Date</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {appState.sessionResults.slice(0, 10).map(result => (
                                <TableRow key={result.id}>
                                  <TableCell className="font-medium">{result.student_name}</TableCell>
                                  <TableCell>{result.student_id}</TableCell>
                                  <TableCell>
                                    <div className="flex items-center gap-2">
                                      <span>{result.total_score}/{result.max_score}</span>
                                      <span className="text-gray-500">({result.percentage}%)</span>
                                    </div>
                                  </TableCell>
                                  <TableCell>
                                    <Badge variant={result.passed ? "default" : "destructive"}>
                                      {result.passed ? "Pass" : "Fail"}
                                    </Badge>
                                  </TableCell>
                                  <TableCell>
                                    {result.requires_manual_review && (
                                      <Badge variant="outline">Manual Review</Badge>
                                    )}
                                  </TableCell>
                                  <TableCell className="text-gray-500">
                                    {new Date(result.evaluated_at).toLocaleDateString()}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                          
                          {appState.sessionResults.length > 10 && (
                            <div className="text-center mt-4">
                              <Button variant="outline">
                                Load More Results
                              </Button>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <BarChart3 className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">No results yet</h3>
                      <p className="text-gray-500 mb-4">
                        {selectedSession 
                          ? "Upload and evaluate some answer sheets to see analytics."
                          : "Select a session to view results and analytics."
                        }
                      </p>
                      {!selectedSession && (
                        <Button onClick={() => setCurrentView('sessions')}>
                          <FileText className="w-4 h-4 mr-2" />
                          View Sessions
                        </Button>
                      )}
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
                    Search for specific students or results across all sessions
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
                              <TableHead>Score</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead>Date</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {filteredResults.map(result => (
                              <TableRow key={result.id}>
                                <TableCell className="font-medium">{result.student_name}</TableCell>
                                <TableCell>{result.student_id}</TableCell>
                                <TableCell>
                                  <div className="flex items-center gap-2">
                                    <span>{result.total_score}/{result.max_score}</span>
                                    <span className="text-gray-500">({result.percentage}%)</span>
                                  </div>
                                </TableCell>
                                <TableCell>
                                  <Badge variant={result.passed ? "default" : "destructive"}>
                                    {result.passed ? "Pass" : "Fail"}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-gray-500">
                                  {new Date(result.evaluated_at).toLocaleDateString()}
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

            {/* Manual Review View */}
            {currentView === 'manual' && (
              <Card className="bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Edit className="w-6 h-6 text-purple-600" />
                    Manual Review Queue
                  </CardTitle>
                  <CardDescription>
                    Review evaluations that require manual attention
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {appState.reviewQueue.length > 0 ? (
                    <div className="space-y-4">
                      {appState.reviewQueue.map(review => (
                        <Card key={review.id} className="border-l-4 border-l-yellow-500">
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <h3 className="font-semibold">{review.student_name}</h3>
                                <p className="text-sm text-gray-600">{review.student_id} - {review.session_name}</p>
                                <p className="text-sm text-gray-500">Reason: {review.reason}</p>
                              </div>
                              <div className="text-right">
                                <p className="text-lg font-semibold">{review.original_score} marks</p>
                                <Badge variant="outline">Priority: {review.priority}</Badge>
                              </div>
                            </div>
                            <div className="mt-4 flex gap-2">
                              <Dialog>
                                <DialogTrigger asChild>
                                  <Button size="sm" variant="outline">
                                    <Eye className="w-4 h-4 mr-2" />
                                    Review
                                  </Button>
                                </DialogTrigger>
                                <DialogContent className="max-w-2xl">
                                  <DialogHeader>
                                    <DialogTitle>Manual Review - {review.student_name}</DialogTitle>
                                    <DialogDescription>
                                      Review and adjust the evaluation as needed
                                    </DialogDescription>
                                  </DialogHeader>
                                  <div className="space-y-4">
                                    <div>
                                      <Label>Original Score</Label>
                                      <div className="text-lg font-semibold">{review.original_score} marks</div>
                                    </div>
                                    <div>
                                      <Label htmlFor="manual-score">Manual Score</Label>
                                      <Input
                                        id="manual-score"
                                        type="number"
                                        value={manualScore}
                                        onChange={(e) => setManualScore(e.target.value)}
                                        placeholder="Enter adjusted score"
                                      />
                                    </div>
                                    <div>
                                      <Label htmlFor="review-notes">Review Notes</Label>
                                      <Textarea
                                        id="review-notes"
                                        value={reviewNotes}
                                        onChange={(e) => setReviewNotes(e.target.value)}
                                        placeholder="Add your review comments..."
                                        rows={3}
                                      />
                                    </div>
                                    <Button
                                      onClick={() => {
                                        // Submit manual review
                                        evaluationsApi.submitManualReview(review.id, {
                                          manual_score: parseFloat(manualScore),
                                          reviewer_notes: reviewNotes
                                        }).then(() => {
                                          toast({
                                            title: "Review Submitted",
                                            description: "Manual review has been saved successfully."
                                          });
                                          setManualScore('');
                                          setReviewNotes('');
                                          // Refresh review queue
                                          evaluationsApi.getReviewQueue().then(data => {
                                            setAppState(prev => ({ ...prev, reviewQueue: data.reviews }));
                                          });
                                        }).catch(error => {
                                          toast({
                                            title: "Error",
                                            description: error.message,
                                            variant: "destructive"
                                          });
                                        });
                                      }}
                                      className="bg-gradient-to-r from-green-500 to-blue-500"
                                    >
                                      <Save className="w-4 h-4 mr-2" />
                                      Submit Review
                                    </Button>
                                  </div>
                                </DialogContent>
                              </Dialog>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Edit className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold text-gray-600 mb-2">No reviews pending</h3>
                      <p className="text-gray-500">All evaluations are complete and don't require manual review.</p>
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
                    Settings & Profile
                  </CardTitle>
                  <CardDescription>
                    Manage your account settings and preferences
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* User Profile */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Profile Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Label>Full Name</Label>
                          <div className="text-lg font-medium">{appState.user?.full_name}</div>
                        </div>
                        <div>
                          <Label>Email</Label>
                          <div className="text-lg font-medium">{appState.user?.email}</div>
                        </div>
                        <div>
                          <Label>University</Label>
                          <div className="text-lg font-medium">{appState.user?.university}</div>
                        </div>
                        <div>
                          <Label>Department</Label>
                          <div className="text-lg font-medium">{appState.user?.department}</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Statistics */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Usage Statistics</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Schemes:</span>
                        <span className="font-semibold">{appState.schemes.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Active Sessions:</span>
                        <span className="font-semibold">{appState.sessions.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Evaluations:</span>
                        <span className="font-semibold">{appState.sessionResults.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Pending Reviews:</span>
                        <span className="font-semibold">{appState.reviewQueue.length}</span>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Actions */}
                  <div className="flex gap-4">
                    <Button variant="outline" onClick={handleLogout}>
                      <LogOut className="w-4 h-4 mr-2" />
                      Logout
                    </Button>
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
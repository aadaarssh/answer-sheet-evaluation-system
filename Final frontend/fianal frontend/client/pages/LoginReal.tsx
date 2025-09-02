import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, Rocket, LogIn, User, CheckCircle, UserPlus, AlertCircle } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "@/hooks/use-toast";
import { authApi, type User as UserType } from "../services/api";

interface LoginProps {
  onLogin: (user: UserType) => void;
}

type AuthMode = 'login' | 'register' | 'loading';

export default function LoginReal({ onLogin }: LoginProps) {
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string>('');
  
  // Login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  
  // Registration form
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regFullName, setRegFullName] = useState("");
  const [regUniversity, setRegUniversity] = useState("");
  const [regDepartment, setRegDepartment] = useState("");

  // Check if user is already authenticated
  useEffect(() => {
    if (authApi.isAuthenticated()) {
      handleAutoLogin();
    }
  }, []);

  const handleAutoLogin = async () => {
    try {
      setAuthMode('loading');
      const user = await authApi.getCurrentUser();
      onLogin(user);
    } catch (error) {
      // Token might be expired, clear it
      authApi.logout();
      setAuthMode('login');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!loginEmail || !loginPassword) {
      setError('Please enter both email and password');
      return;
    }

    try {
      setAuthMode('loading');
      
      // Animate progress bar
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 100);

      await authApi.login({ username: loginEmail, password: loginPassword });
      const user = await authApi.getCurrentUser();
      
      clearInterval(progressInterval);
      setProgress(100);
      
      setTimeout(() => {
        onLogin(user);
        toast({
          title: "Login Successful",
          description: `Welcome back, ${user.full_name}!`,
        });
      }, 500);

    } catch (error) {
      setAuthMode('login');
      setProgress(0);
      setError(error instanceof Error ? error.message : 'Login failed');
      toast({
        title: "Login Failed",
        description: error instanceof Error ? error.message : 'Login failed',
        variant: "destructive"
      });
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!regEmail || !regPassword || !regFullName || !regUniversity || !regDepartment) {
      setError('Please fill in all fields');
      return;
    }

    if (regPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    try {
      setAuthMode('loading');
      
      // Animate progress bar
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 8, 90));
      }, 100);

      await authApi.register({
        email: regEmail,
        password: regPassword,
        full_name: regFullName,
        university: regUniversity,
        department: regDepartment
      });

      // Auto-login after registration
      await authApi.login({ username: regEmail, password: regPassword });
      const user = await authApi.getCurrentUser();
      
      clearInterval(progressInterval);
      setProgress(100);
      
      setTimeout(() => {
        onLogin(user);
        toast({
          title: "Registration Successful",
          description: `Welcome to EvalAI Pro, ${user.full_name}!`,
        });
      }, 500);

    } catch (error) {
      setAuthMode('register');
      setProgress(0);
      setError(error instanceof Error ? error.message : 'Registration failed');
      toast({
        title: "Registration Failed",
        description: error instanceof Error ? error.message : 'Registration failed',
        variant: "destructive"
      });
    }
  };

  const switchMode = () => {
    setAuthMode(authMode === 'login' ? 'register' : 'login');
    setError('');
    setProgress(0);
  };

  if (authMode === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800 relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-400/20 to-blue-400/20 animate-gradient-shift"></div>
        </div>

        {/* Floating Shapes */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute w-20 h-20 bg-white/10 rounded-full top-20 left-10 animate-float" style={{ animationDelay: '0s' }}></div>
          <div className="absolute w-32 h-32 bg-white/10 rounded-full top-60 right-20 animate-float" style={{ animationDelay: '2s' }}></div>
          <div className="absolute w-16 h-16 bg-white/10 rounded-full bottom-20 left-20 animate-float" style={{ animationDelay: '4s' }}></div>
          <div className="absolute w-24 h-24 bg-white/10 rounded-full top-32 right-32 animate-float" style={{ animationDelay: '1s' }}></div>
        </div>

        <Card className="relative z-10 bg-white/95 backdrop-blur-xl shadow-2xl border-white/20 max-w-md w-full mx-4 animate-slide-up">
          <CardContent className="p-12 text-center">
            <div className="w-24 h-24 bg-gradient-to-br from-green-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-8 animate-pulse-glow">
              <CheckCircle className="w-12 h-12 text-white animate-bounce" />
            </div>
            
            <h1 className="text-3xl font-bold text-gradient-primary mb-4">
              {authMode === 'loading' ? 'Authenticating...' : 'Welcome to EvalAI Pro!'}
            </h1>
            
            <p className="text-gray-600 mb-8 text-lg">
              Connecting to your intelligent assessment dashboard...
            </p>
            
            <div className="space-y-4">
              <Progress value={progress} className="h-3 bg-gray-200" />
              <div className="flex items-center justify-center gap-2 text-gray-500">
                <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
                <span>Setting up your workspace</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800 relative overflow-hidden p-4">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-45 from-purple-400/20 via-blue-400/20 to-purple-400/20 animate-gradient-shift"></div>
      </div>

      {/* Floating Shapes */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-20 h-20 bg-white/10 rounded-full top-20 left-10 animate-float" style={{ animationDelay: '0s' }}></div>
        <div className="absolute w-32 h-32 bg-white/10 rounded-full top-60 right-20 animate-float" style={{ animationDelay: '2s' }}></div>
        <div className="absolute w-16 h-16 bg-white/10 rounded-full bottom-20 left-20 animate-float" style={{ animationDelay: '4s' }}></div>
        <div className="absolute w-24 h-24 bg-white/10 rounded-full top-32 right-32 animate-float" style={{ animationDelay: '1s' }}></div>
        <div className="absolute w-28 h-28 bg-white/5 rounded-full bottom-32 right-10 animate-float" style={{ animationDelay: '3s' }}></div>
      </div>

      <Card className="relative z-10 bg-white/95 backdrop-blur-xl shadow-2xl border-white/20 w-full max-w-6xl animate-slide-up">
        <CardContent className="p-0">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
            {/* Login/Register Form */}
            <div className="p-12 lg:p-16">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center">
                  <Brain className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-gradient-primary">
                  EvalAI Pro
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <h1 className="text-4xl font-bold text-gray-800 mb-4">
                    {authMode === 'login' ? 'Welcome Back' : 'Create Account'}
                  </h1>
                  <p className="text-gray-600 text-lg leading-relaxed">
                    {authMode === 'login' 
                      ? 'Sign in to your intelligent assessment platform and unlock the power of AI-driven evaluation.'
                      : 'Join the future of academic evaluation. Create your account to get started with AI-powered assessment.'
                    }
                  </p>
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {/* Login Form */}
                {authMode === 'login' && (
                  <form className="space-y-6" onSubmit={handleLogin}>
                    <div className="space-y-2">
                      <Label htmlFor="login-email" className="text-base font-semibold">Email Address</Label>
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="Enter your email"
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="login-password" className="text-base font-semibold">Password</Label>
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="Enter your password"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                        required
                      />
                    </div>

                    <div className="flex flex-col gap-4 pt-4">
                      <Button 
                        type="submit"
                        className="h-12 text-base font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl"
                      >
                        <LogIn className="w-5 h-5 mr-2" />
                        Sign In
                      </Button>
                      
                      <Button 
                        type="button"
                        variant="outline"
                        onClick={switchMode}
                        className="h-12 text-base font-semibold border-2 border-purple-300 text-purple-700 hover:bg-purple-50 transition-all duration-300 transform hover:scale-[1.02]"
                      >
                        <UserPlus className="w-5 h-5 mr-2" />
                        Create New Account
                      </Button>
                    </div>
                  </form>
                )}

                {/* Registration Form */}
                {authMode === 'register' && (
                  <form className="space-y-6" onSubmit={handleRegister}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="reg-name" className="text-base font-semibold">Full Name</Label>
                        <Input
                          id="reg-name"
                          type="text"
                          placeholder="Dr. John Smith"
                          value={regFullName}
                          onChange={(e) => setRegFullName(e.target.value)}
                          className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="reg-email" className="text-base font-semibold">Email Address</Label>
                        <Input
                          id="reg-email"
                          type="email"
                          placeholder="john@university.edu"
                          value={regEmail}
                          onChange={(e) => setRegEmail(e.target.value)}
                          className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="reg-university" className="text-base font-semibold">University</Label>
                        <Input
                          id="reg-university"
                          type="text"
                          placeholder="Stanford University"
                          value={regUniversity}
                          onChange={(e) => setRegUniversity(e.target.value)}
                          className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="reg-department" className="text-base font-semibold">Department</Label>
                        <Input
                          id="reg-department"
                          type="text"
                          placeholder="Computer Science"
                          value={regDepartment}
                          onChange={(e) => setRegDepartment(e.target.value)}
                          className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                          required
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="reg-password" className="text-base font-semibold">Password</Label>
                      <Input
                        id="reg-password"
                        type="password"
                        placeholder="Enter a secure password"
                        value={regPassword}
                        onChange={(e) => setRegPassword(e.target.value)}
                        className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                        required
                        minLength={6}
                      />
                      <p className="text-sm text-gray-500">Password must be at least 6 characters long</p>
                    </div>

                    <div className="flex flex-col gap-4 pt-4">
                      <Button 
                        type="submit"
                        className="h-12 text-base font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl"
                      >
                        <UserPlus className="w-5 h-5 mr-2" />
                        Create Account
                      </Button>
                      
                      <Button 
                        type="button"
                        variant="outline"
                        onClick={switchMode}
                        className="h-12 text-base font-semibold border-2 border-purple-300 text-purple-700 hover:bg-purple-50 transition-all duration-300 transform hover:scale-[1.02]"
                      >
                        <LogIn className="w-5 h-5 mr-2" />
                        Back to Sign In
                      </Button>
                    </div>
                  </form>
                )}
              </div>
            </div>

            {/* Feature Showcase */}
            <div className="bg-gradient-to-br from-purple-50 via-blue-50 to-purple-100 p-12 lg:p-16 flex flex-col justify-center items-center text-center">
              <div className="w-32 h-32 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-8 animate-pulse-glow">
                <Rocket className="w-16 h-16 text-white animate-bounce" />
              </div>

              <h3 className="text-2xl font-bold text-gray-800 mb-6">Powerful Features</h3>
              
              <ul className="space-y-4 text-left max-w-sm">
                {[
                  "AI-powered automatic evaluation",
                  "OpenAI Vision API integration", 
                  "Real-time analytics & reports",
                  "Manual review capabilities",
                  "Secure cloud storage",
                  "Multi-subject management"
                ].map((feature, index) => (
                  <li key={index} className="flex items-center gap-3 text-gray-700 animate-slide-in-right" style={{ animationDelay: `${index * 0.1}s` }}>
                    <div className="w-2 h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-pulse"></div>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
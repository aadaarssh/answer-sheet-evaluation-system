import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Brain, Rocket, LogIn, User, CheckCircle } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface LoginProps {
  onLogin: (name: string, email: string) => void;
}

export default function Login({ onLogin }: LoginProps) {
  const [showWelcome, setShowWelcome] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [progress, setProgress] = useState(0);

  const handleSignIn = () => {
    const userEmail = email || 'user@evalai.com';
    const userName = userEmail.split('@')[0];
    
    setShowWelcome(true);
    
    // Animate progress bar
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          setTimeout(() => onLogin(userName, userEmail), 500);
          return 100;
        }
        return prev + 2;
      });
    }, 50);
  };

  const handleGuestLogin = () => {
    setShowWelcome(true);
    
    // Animate progress bar
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          setTimeout(() => onLogin('Guest', 'guest@evalai.com'), 500);
          return 100;
        }
        return prev + 2;
      });
    }, 50);
  };

  if (showWelcome) {
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
              Welcome to EvalAI Pro!
            </h1>
            
            <p className="text-gray-600 mb-8 text-lg">
              You're all set! Initializing your intelligent assessment dashboard...
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
            {/* Login Form */}
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
                  <h1 className="text-4xl font-bold text-gray-800 mb-4">Welcome Back</h1>
                  <p className="text-gray-600 text-lg leading-relaxed">
                    Sign in to your intelligent assessment platform and unlock the power of AI-driven evaluation.
                  </p>
                </div>

                <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); handleSignIn(); }}>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-base font-semibold">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="Enter your email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-base font-semibold">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="h-12 text-base border-2 focus:border-purple-500 transition-all duration-300"
                    />
                  </div>

                  <div className="flex flex-col sm:flex-row gap-4 pt-4">
                    <Button 
                      type="submit"
                      className="h-12 text-base font-semibold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 transition-all duration-300 transform hover:scale-[1.02] hover:shadow-xl flex-1"
                    >
                      <LogIn className="w-5 h-5 mr-2" />
                      Sign In
                    </Button>
                    
                    <Button 
                      type="button"
                      variant="outline"
                      onClick={handleGuestLogin}
                      className="h-12 text-base font-semibold border-2 border-purple-300 text-purple-700 hover:bg-purple-50 transition-all duration-300 transform hover:scale-[1.02] flex-1"
                    >
                      <User className="w-5 h-5 mr-2" />
                      Continue as Guest
                    </Button>
                  </div>
                </form>
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
                  "Drag & drop file uploads", 
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

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { Home, Brain, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-purple-800 flex items-center justify-center p-4">
      {/* Animated Background */}
      <div className="fixed inset-0 opacity-30">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-400/20 to-blue-400/20 animate-pulse"></div>
      </div>

      <Card className="relative z-10 max-w-lg w-full bg-white/95 backdrop-blur-lg shadow-xl border-white/20">
        <CardHeader className="text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <Brain className="w-10 h-10 text-white" />
          </div>
          <CardTitle className="text-2xl bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Page Not Found
          </CardTitle>
          <CardDescription className="text-lg">
            Oops! The page you're looking for doesn't exist in EvalAI Pro.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-6">
          <div className="text-6xl font-bold text-gray-300">404</div>
          <p className="text-gray-600">
            This page might be under construction or you may have followed an invalid link.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700">
              <Link to="/">
                <Home className="w-4 h-4 mr-2" />
                Go Home
              </Link>
            </Button>
            <Button variant="outline" onClick={() => window.history.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

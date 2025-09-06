import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Brain, 
  Database, 
  Image, 
  Eye, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Loader2, 
  AlertTriangle,
  Wifi,
  WifiOff
} from "lucide-react";

// Types for processing updates
interface ProcessingStage {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  estimatedTime: number; // in seconds
}

interface ProcessingUpdate {
  script_id: string;
  status: 'processing' | 'completed' | 'failed';
  stage: string;
  progress: number;
  stage_description: string;
  estimated_remaining_time: number;
  details?: Record<string, any>;
  result?: Record<string, any>;
  error?: string;
  timestamp: number;
}

interface ScriptProcessingState {
  script_id: string;
  script_name: string;
  student_name: string;
  current_stage: string;
  progress: number;
  status: 'processing' | 'completed' | 'failed' | 'pending';
  stage_description: string;
  estimated_remaining_time: number;
  details: Record<string, any>;
  result?: Record<string, any>;
  error?: string;
  started_at: number;
  completed_at?: number;
}

// Processing stages configuration
const PROCESSING_STAGES: ProcessingStage[] = [
  {
    id: 'database_connected',
    name: 'Database',
    description: 'Connecting to database and validating script',
    icon: Database,
    estimatedTime: 2
  },
  {
    id: 'image_validated',
    name: 'Image Validation',
    description: 'Validating image file and format',
    icon: Image,
    estimatedTime: 3
  },
  {
    id: 'ocr_completed',
    name: 'OCR Processing',
    description: 'Extracting text using OpenAI Vision API',
    icon: Eye,
    estimatedTime: 20
  },
  {
    id: 'evaluation_completed',
    name: 'AI Evaluation',
    description: 'Evaluating answers with AI semantic analysis',
    icon: Brain,
    estimatedTime: 25
  },
  {
    id: 'verification_completed',
    name: 'Verification',
    description: 'Verifying results with Gemini AI',
    icon: CheckCircle,
    estimatedTime: 15
  },
  {
    id: 'completed',
    name: 'Complete',
    description: 'All processing completed successfully',
    icon: CheckCircle,
    estimatedTime: 0
  }
];

interface ProcessingDashboardProps {
  sessionId?: string;
  onProcessingComplete?: (result: any) => void;
}

interface WebSocketManager {
  connect: () => void;
  disconnect: () => void;
  subscribe: (scriptId: string) => void;
  isConnected: boolean;
}

const ProcessingDashboard: React.FC<ProcessingDashboardProps> = ({
  sessionId,
  onProcessingComplete
}) => {
  const [processingScripts, setProcessingScripts] = useState<Map<string, ScriptProcessingState>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    try {
      const wsUrl = `ws://localhost:8000/api/ws`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setConnectionError(null);
        console.log('WebSocket connected');

        // Subscribe to session updates if sessionId is provided
        if (sessionId) {
          ws.send(JSON.stringify({
            type: 'subscribe_session',
            session_id: sessionId
          }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('WebSocket disconnected');
        
        // Attempt to reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        setConnectionError('WebSocket connection failed');
        console.error('WebSocket error:', error);
      };

      setWebsocket(ws);
    } catch (error) {
      setConnectionError('Failed to establish WebSocket connection');
      console.error('WebSocket setup error:', error);
    }
  }, [sessionId]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (data: any) => {
    if (data.type === 'script_update') {
      const update: ProcessingUpdate = data;
      updateScriptProcessing(update);
    } else if (data.type === 'session_update') {
      // Handle session-level updates
      console.log('Session update:', data);
    } else if (data.type === 'connection_established') {
      console.log('WebSocket connection established:', data.connection_id);
    }
  };

  // Update script processing state
  const updateScriptProcessing = (update: ProcessingUpdate) => {
    setProcessingScripts(prev => {
      const newMap = new Map(prev);
      const existing = newMap.get(update.script_id);

      const updatedState: ScriptProcessingState = {
        script_id: update.script_id,
        script_name: update.details?.script_name || existing?.script_name || 'Unknown',
        student_name: update.details?.student_name || existing?.student_name || 'Unknown',
        current_stage: update.stage,
        progress: update.progress,
        status: update.status,
        stage_description: update.stage_description,
        estimated_remaining_time: update.estimated_remaining_time,
        details: { ...existing?.details, ...update.details },
        result: update.result,
        error: update.error,
        started_at: existing?.started_at || update.timestamp,
        completed_at: update.status === 'completed' ? update.timestamp : existing?.completed_at
      };

      newMap.set(update.script_id, updatedState);

      // Call completion callback if processing is done
      if (update.status === 'completed' && onProcessingComplete && update.result) {
        onProcessingComplete(update.result);
      }

      return newMap;
    });
  };

  // Subscribe to a specific script
  const subscribeToScript = (scriptId: string) => {
    if (websocket && isConnected) {
      websocket.send(JSON.stringify({
        type: 'subscribe_script',
        script_id: scriptId
      }));
    }
  };

  // Format time remaining
  const formatTimeRemaining = (seconds: number): string => {
    if (seconds <= 0) return 'Almost done...';
    
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    if (mins > 0) {
      return `${mins}m ${secs}s remaining`;
    }
    return `${secs}s remaining`;
  };

  // Get stage progress for visual indicators
  const getStageProgress = (currentStage: string): { completed: number; current: number; total: number } => {
    const stageIndex = PROCESSING_STAGES.findIndex(s => s.id === currentStage);
    return {
      completed: Math.max(0, stageIndex),
      current: stageIndex >= 0 ? stageIndex : 0,
      total: PROCESSING_STAGES.length
    };
  };

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (websocket) {
        websocket.close();
      }
    };
  }, [connectWebSocket]);

  // Render individual script processing card
  const renderScriptCard = (script: ScriptProcessingState) => {
    const stageProgress = getStageProgress(script.current_stage);
    const currentStageInfo = PROCESSING_STAGES.find(s => s.id === script.current_stage);
    const CurrentStageIcon = currentStageInfo?.icon || Loader2;

    return (
      <Card key={script.script_id} className="mb-4 border-l-4 border-l-blue-500">
        <CardHeader className="pb-3">
          <div className="flex justify-between items-start">
            <div>
              <CardTitle className="text-lg flex items-center gap-2">
                {script.status === 'processing' ? (
                  <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                ) : script.status === 'completed' ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                {script.student_name}
              </CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1">
                <span>{script.script_name}</span>
                <Badge variant="outline" className="text-xs">
                  {script.script_id.slice(-8)}
                </Badge>
              </CardDescription>
            </div>
            <Badge variant={
              script.status === 'completed' ? 'default' : 
              script.status === 'failed' ? 'destructive' : 'secondary'
            }>
              {script.status === 'processing' ? 'Processing' : 
               script.status === 'completed' ? 'Complete' : 'Failed'}
            </Badge>
          </div>
        </CardHeader>
        
        <CardContent>
          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Overall Progress</span>
              <span className="text-sm text-gray-500">{script.progress}%</span>
            </div>
            <Progress value={script.progress} className="h-3" />
          </div>

          {/* Current Stage */}
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <CurrentStageIcon className={`w-4 h-4 ${script.status === 'processing' ? 'animate-pulse' : ''}`} />
              <span className="text-sm font-medium">Current Stage</span>
            </div>
            <p className="text-sm text-gray-600 ml-6">{script.stage_description}</p>
          </div>

          {/* Time Estimate */}
          {script.status === 'processing' && script.estimated_remaining_time > 0 && (
            <div className="flex items-center gap-2 mb-4 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              {formatTimeRemaining(script.estimated_remaining_time)}
            </div>
          )}

          {/* Stage Progress Indicators */}
          <div className="grid grid-cols-6 gap-2 mb-4">
            {PROCESSING_STAGES.map((stage, index) => {
              const StageIcon = stage.icon;
              const isCompleted = index < stageProgress.completed;
              const isCurrent = index === stageProgress.current;
              const isPending = index > stageProgress.current;

              return (
                <div
                  key={stage.id}
                  className={`flex flex-col items-center p-2 rounded-lg text-xs ${
                    isCompleted ? 'bg-green-100 text-green-700' :
                    isCurrent ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-400'
                  }`}
                >
                  <StageIcon className={`w-4 h-4 mb-1 ${
                    isCurrent && script.status === 'processing' ? 'animate-pulse' : ''
                  }`} />
                  <span className="text-center leading-tight">{stage.name}</span>
                </div>
              );
            })}
          </div>

          {/* Error Display */}
          {script.error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{script.error}</AlertDescription>
            </Alert>
          )}

          {/* Results Display */}
          {script.result && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-semibold text-green-800 mb-2">Processing Complete!</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-green-600">Score:</span>
                  <span className="ml-2 font-medium">
                    {script.result.total_score}/{script.result.max_score} ({script.result.percentage}%)
                  </span>
                </div>
                <div>
                  <span className="text-green-600">OCR Confidence:</span>
                  <span className="ml-2 font-medium">{(script.result.ocr_confidence * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-green-600">Questions:</span>
                  <span className="ml-2 font-medium">{script.result.questions_extracted}</span>
                </div>
                <div>
                  <span className="text-green-600">Processing Time:</span>
                  <span className="ml-2 font-medium">{script.result.processing_time?.toFixed(1)}s</span>
                </div>
              </div>
              {script.result.requires_manual_review && (
                <Badge variant="destructive" className="mt-2">
                  Requires Manual Review
                </Badge>
              )}
            </div>
          )}

          {/* Processing Details */}
          {script.details && Object.keys(script.details).length > 0 && (
            <details className="mt-4">
              <summary className="text-sm font-medium cursor-pointer text-gray-600">
                Processing Details
              </summary>
              <div className="mt-2 text-xs text-gray-500 bg-gray-50 p-3 rounded">
                <pre>{JSON.stringify(script.details, null, 2)}</pre>
              </div>
            </details>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-600" />
              Real-Time Processing Dashboard
            </CardTitle>
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Badge variant="default" className="flex items-center gap-1">
                  <Wifi className="w-3 h-3" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="destructive" className="flex items-center gap-1">
                  <WifiOff className="w-3 h-3" />
                  Disconnected
                </Badge>
              )}
            </div>
          </div>
          <CardDescription>
            Monitor real-time processing of answer scripts with live updates and progress tracking
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Connection Error */}
      {connectionError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            {connectionError}. The dashboard will attempt to reconnect automatically.
          </AlertDescription>
        </Alert>
      )}

      {/* Processing Scripts */}
      {processingScripts.size > 0 ? (
        <div>
          <h3 className="text-lg font-semibold mb-4">
            Processing Scripts ({processingScripts.size})
          </h3>
          {Array.from(processingScripts.values())
            .sort((a, b) => b.started_at - a.started_at)
            .map(renderScriptCard)}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Brain className="w-12 h-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-semibold text-gray-600 mb-2">No Active Processing</h3>
            <p className="text-gray-500 text-center">
              Upload answer scripts to see real-time processing updates here.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ProcessingDashboard;
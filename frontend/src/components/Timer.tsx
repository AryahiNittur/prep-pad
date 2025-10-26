import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  LinearProgress,
  Alert,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

interface TimerProps {
  instruction: string;
  onComplete?: () => void;
  autoStart?: boolean;
  shouldPause?: boolean;
  shouldResume?: boolean;
}

interface TimerState {
  isActive: boolean;
  isPaused: boolean;
  timeLeft: number;
  totalTime: number;
}

const Timer: React.FC<TimerProps> = ({ instruction, onComplete, autoStart = false, shouldPause = false, shouldResume = false }) => {
  const [timerState, setTimerState] = useState<TimerState>({
    isActive: false,
    isPaused: false,
    timeLeft: 0,
    totalTime: 0,
  });
  const [showTimer, setShowTimer] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize timer when instruction changes
  useEffect(() => {
    // Regex patterns to detect time mentions in instructions
    const timePatterns = [
      /(\d+)\s*minutes?/gi,
      /(\d+)\s*mins?/gi,
      /(\d+)\s*min/gi,
      /for\s*(\d+)\s*minutes?/gi,
      /cook\s*for\s*(\d+)\s*minutes?/gi,
      /bake\s*for\s*(\d+)\s*minutes?/gi,
      /simmer\s*for\s*(\d+)\s*minutes?/gi,
      /boil\s*for\s*(\d+)\s*minutes?/gi,
    ];

    const extractTime = (text: string): number | null => {
      for (const pattern of timePatterns) {
        const match = text.match(pattern);
        if (match) {
          const timeStr = match[1] || match[0].match(/\d+/)?.[0];
          if (timeStr) {
            const time = parseInt(timeStr, 10);
            if (time > 0 && time <= 300) {
              return time;
            }
          }
        }
      }
      return null;
    };

    const timeInMinutes = extractTime(instruction);
    if (timeInMinutes) {
      setShowTimer(true);
      setTimerState({
        isActive: false,
        isPaused: false,
        timeLeft: timeInMinutes * 60,
        totalTime: timeInMinutes * 60,
      });
    } else {
      setShowTimer(false);
    }
  }, [instruction]);

  // Handle auto-start timer
  useEffect(() => {
    if (autoStart && timerState.totalTime > 0 && !timerState.isActive) {
      setTimerState(prev => ({ ...prev, isActive: true, isPaused: false }));
    }
  }, [autoStart, timerState.totalTime, timerState.isActive]);

  // Handle pause/resume from voice commands
  useEffect(() => {
    if (shouldPause && timerState.isActive && !timerState.isPaused) {
      setTimerState(prev => ({ ...prev, isPaused: true }));
    }
    if (shouldResume && timerState.isActive && timerState.isPaused) {
      setTimerState(prev => ({ ...prev, isPaused: false }));
    }
  }, [shouldPause, shouldResume, timerState.isActive, timerState.isPaused]);

  // Timer countdown logic
  useEffect(() => {
    if (timerState.isActive && !timerState.isPaused && timerState.timeLeft > 0) {
      intervalRef.current = setInterval(() => {
        setTimerState(prev => {
          const newTimeLeft = prev.timeLeft - 1;
          if (newTimeLeft <= 0) {
            // Timer completed
            playBeep();
            if (onComplete) {
              onComplete();
            }
            return {
              ...prev,
              isActive: false,
              timeLeft: 0,
            };
          }
          return {
            ...prev,
            timeLeft: newTimeLeft,
          };
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [timerState.isActive, timerState.isPaused, timerState.timeLeft, onComplete]);

  // Play beep sound when timer completes
  const playBeep = () => {
    try {
      // Create audio context for beep sound
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.warn('Could not play beep sound:', error);
    }
  };

  const startTimer = () => {
    setTimerState(prev => ({ ...prev, isActive: true, isPaused: false }));
  };

  const pauseTimer = () => {
    setTimerState(prev => ({ ...prev, isPaused: !prev.isPaused }));
  };

  const stopTimer = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setTimerState(prev => ({
      ...prev,
      isActive: false,
      isPaused: false,
      timeLeft: prev.totalTime,
    }));
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const progress = timerState.totalTime > 0 ? (timerState.timeLeft / timerState.totalTime) * 100 : 0;

  if (!showTimer) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
      >
        <Card sx={{ mb: 2, border: '2px solid', borderColor: 'primary.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <TimerIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" component="h3">
                Timer Detected
              </Typography>
            </Box>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              This step mentions a time duration. Start the timer when you begin this step.
            </Typography>

            <Box sx={{ textAlign: 'center', mb: 2 }}>
              <Typography variant="h3" component="div" sx={{ fontFamily: 'monospace', mb: 1 }}>
                {formatTime(timerState.timeLeft)}
              </Typography>
              
              <LinearProgress
                variant="determinate"
                value={progress}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  mb: 2,
                  backgroundColor: 'rgba(0,0,0,0.1)',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: timerState.timeLeft <= 30 ? 'error.main' : 'primary.main',
                  },
                }}
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
              {!timerState.isActive ? (
                <Button
                  variant="contained"
                  startIcon={<PlayIcon />}
                  onClick={startTimer}
                  color="primary"
                >
                  Start Timer
                </Button>
              ) : (
                <>
                  <Button
                    variant="outlined"
                    startIcon={timerState.isPaused ? <PlayIcon /> : <PauseIcon />}
                    onClick={pauseTimer}
                  >
                    {timerState.isPaused ? 'Resume' : 'Pause'}
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<StopIcon />}
                    onClick={stopTimer}
                    color="error"
                  >
                    Stop
                  </Button>
                </>
              )}
            </Box>

            {timerState.timeLeft === 0 && timerState.isActive === false && (
              <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
              <Alert severity="success" sx={{ mt: 2 }}>
                <Typography variant="h6">⏰ Time's up!</Typography>
                <Typography variant="body2">
                  The timer has completed. You can proceed to the next step.
                </Typography>
              </Alert>
              </Box>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </AnimatePresence>
  );
};

export default Timer;

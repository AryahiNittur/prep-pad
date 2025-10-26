import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useSpeechSynthesis, useSpeechRecognition } from 'react-speech-kit';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  Fab,
  Alert,
} from '@mui/material';
import {
  SkipNext as NextIcon,
  Replay as RepeatIcon,
  Mic as MicIcon,
  Kitchen as KitchenIcon,
  Timer as TimerIcon,
  Restaurant as RestaurantIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import Timer from '../components/Timer';

interface SessionData {
  session_id: number;
  recipe_title: string;
  current_step: string;
  current_phase: string;
  is_active: boolean;
  started_at: string;
}

interface VoiceResponse {
  response: string;
  current_step?: string;
  current_phase?: string;
  is_complete?: boolean;
}

const CookingSession: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [first, setFirst] = useState(true);
  const [voiceCommand, setVoiceCommand] = useState('');
  const [lastResponse, setLastResponse] = useState<string | null>(null);
  const [newRecipeCreated, setNewRecipeCreated] = useState<{id: number, title: string} | null>(null);

  const [isWakeWordMode, setIsWakeWordMode] = useState(false);
  const isWakeWordModeRef = useRef(isWakeWordMode);

  useEffect(() => {
    isWakeWordModeRef.current = isWakeWordMode;
  }, [isWakeWordMode]);

  const { speak, cancel, voices } = useSpeechSynthesis();
  const [timeoutId, setTimeoutId] = useState<NodeJS.Timeout | null>(null);
  const [timestamp, setTimestamp] = useState(0);
  const [shouldStartTimer, setShouldStartTimer] = useState(false);
  const [shouldPauseTimer, setShouldPauseTimer] = useState(false);
  const [shouldResumeTimer, setShouldResumeTimer] = useState(false);

  const { listen, listening, stop } = useSpeechRecognition({
    onResult: (result) => {
      const speechText = result.toString().toLowerCase();
      setVoiceCommand(speechText);
      console.log('onresult');
      console.log(`${isWakeWordModeRef.current}`);
      if (isWakeWordModeRef.current) {
        // Check for wake word
        if (speechText.includes('hey prep')) {
          console.log('1set');
          setTimeout(() => {
            setIsWakeWordMode(false);
            setVoiceCommand('');
            setTimestamp(Date.now());
          }, 500);
          //stop();
        }
      } else {
        // Actually stop listening and restart for wake word mode
        /*
        stop();
        setTimeout(() => {
          console.log('1listen');
          listen({ interimResults: true, lang: 'en-US' });
          }, 500);*/
          
        console.log('in else');
        // Reset timeout when we get new speech input during command mode
        const newTimeoutId = setTimeout(() => {
          console.log('RESETER');
          // Actually stop listening and restart for wake word mode
          stop();
          //setVoiceCommand('');
          console.log('2set');
          //setIsWakeWordMode(true);
        }, 3000); // Return to wake word mode after 3 seconds of silence
        console.log('setid');
        setTimeoutId(newTimeoutId);
      }
    },
    onEnd: () => {
      if (timeoutId) {
        console.log('clearid');
        clearTimeout(timeoutId);
        setTimeoutId(null);
      }
      
      if (!isWakeWordModeRef.current && voiceCommand.trim()) {
        sendVoiceCommand(voiceCommand);
      }
      // Return to wake word mode after processing command
      setTimeout(() => {
        setVoiceCommand('');
        console.log('3set');
        setIsWakeWordMode(true);
      }, 2000);
    },
  });

  const voiceToFind = 'Google US English';
  const voice = useMemo(() => {
    const voiceIndex = voices.findIndex(voice => voice.name === voiceToFind);
    // Fallback to first available voice if preferred voice not found
    return voiceIndex !== -1 ? voiceIndex : 0;
  }, [voices, voiceToFind]);

  const fetchSession = useCallback(async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/cooking_session/${sessionId}`);
      const sessionData = response.data;
      setSession(sessionData);
      console.log('session set');
      
      // Speak the first step on startup
    } catch (error) {
      console.error('Failed to fetch session:', error);
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      fetchSession();
    }
  }, [sessionId, fetchSession]);

  useEffect(() => {
    if (first && session) {
      setFirst(false);
      speak({ text: `Welcome to your cooking session. ${session.current_step}`, voice: voices[voice] });
      console.log('welcome message spoken');
      console.log('retard set');
      setIsWakeWordMode(true);
    }
  }, [first, session, speak, voices, voice]);

  useEffect(() => {
    if (isWakeWordModeRef.current) {
      console.log('1stop');
      stop();
      setTimeout(() => {
        console.log('newlisten');
        listen({ interimResults: true, lang: 'en-US' });
      }, 500);
    }
  }, [isWakeWordMode, listen, stop]);
  
  // Cleanup timeout on unmount
  /*
  useEffect(() => {
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [timeoutId]); */

  // Start listening on mount with delay to ensure component is ready
  /*
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!listening) {
        console.log('2listen');
        listen({ interimResults: true, lang: 'en-US' });
      }
    }, 1000); // 1 second delay to ensure component is fully mounted

    return () => clearTimeout(timer);
  }, [listening, listen]); // Include dependencies
  */

  const sendVoiceCommand = async (command: string) => {
    if (!sessionId) return;

    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/api/voice_command', {
        command: command,
        session_id: parseInt(sessionId),
      });

      const voiceResponse: VoiceResponse = response.data;
      setLastResponse(voiceResponse.response);
      
      // Check if a new recipe was created
      if ((voiceResponse as any).new_recipe_id && (voiceResponse as any).success) {
        setNewRecipeCreated({
          id: (voiceResponse as any).new_recipe_id,
          title: (voiceResponse as any).modified_recipe?.title || 'Modified Recipe'
        });
      }
      
      // Update session if provided
      const stepChanged = voiceResponse.current_step && 
                         (voiceResponse.current_step !== session?.current_step);
      
      if (voiceResponse.current_step) {
        setSession(prev => prev ? {
          ...prev,
          current_step: voiceResponse.current_step!,
          current_phase: voiceResponse.current_phase || prev.current_phase,
          is_active: !voiceResponse.is_complete,
        } : null);
      }

      // Check if we should start the timer
      if (command === 'start timer' && (voiceResponse as any).should_start_timer) {
        setShouldStartTimer(true);
        setTimestamp(Date.now()); // Trigger Timer component update
      } else if (stepChanged) {
        // Reset timer state only when step changes (not when wake word is detected)
        setShouldStartTimer(false);
        setShouldPauseTimer(false);
        setShouldResumeTimer(false);
        setTimestamp(0);
      }
      
      // Check if we should pause the timer
      if ((command === 'pause timer' || command === 'stop timer') && (voiceResponse as any).should_pause_timer) {
        setShouldPauseTimer(true);
        setShouldResumeTimer(false);
        // Don't update timestamp for pause - it would reset the timer
      }
      
      // Check if we should resume the timer
      if ((command === 'resume timer' || command === 'restart timer' || command === 'continue timer') && (voiceResponse as any).should_resume_timer) {
        setShouldResumeTimer(true);
        setShouldPauseTimer(false);
        // Don't update timestamp for resume - it would reset the timer
      }

      cancel();
      console.log('2Available voices:', voices.map(v => v.name));
      console.log('Using voice index:', voice);
      if (voices.length > 0) {
        speak({ text: voiceResponse.response, voice: voices[voice] });
      } else {
        console.warn('No voices available for speech synthesis');
        // Fallback to default voice
        speak({ text: voiceResponse.response });
      }

      // Clear voice command after processing
      setVoiceCommand('');
    } catch (error) {
      console.error('Failed to send voice command:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSpeechRecognition = () => {
    if (listening) {
      console.log('2stop');
      stop();
      /*
      if (timeoutId) {
        clearTimeout(timeoutId);
        setTimeoutId(null);
      }
      setIsWakeWordMode(true);
      */
    } else {
      setVoiceCommand('');
      console.log('lastset');
      setIsWakeWordMode(false);
      console.log('3listen');
      listen({ interimResults: false, lang: 'en-US' });
    }
  };

  const quickCommands = [
    { command: 'next', label: 'Next Step', icon: <NextIcon /> },
    { command: 'repeat', label: 'Repeat', icon: <RepeatIcon /> },
    { command: 'what prep', label: 'What Prep?', icon: <KitchenIcon /> },
    { command: 'time', label: 'Time Left', icon: <TimerIcon /> },
    { command: 'make vegetarian', label: 'Make Vegetarian', icon: <RestaurantIcon /> },
    { command: 'make vegan', label: 'Make Vegan', icon: <RestaurantIcon /> },
    { command: 'make gluten free', label: 'Make Gluten-Free', icon: <RestaurantIcon /> },
    { command: 'make dairy free', label: 'Make Dairy-Free', icon: <RestaurantIcon /> },
    { command: 'scale up', label: 'Double Recipe', icon: <KitchenIcon /> },
    { command: 'scale down', label: 'Half Recipe', icon: <KitchenIcon /> },
  ];

  if (!session) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography>Loading cooking session...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <style>
        {`
          @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
          }
        `}
      </style>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Session Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            {session.recipe_title}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
            <Chip
              label={session.current_phase === 'prep' ? 'Prep Phase' : 'Cooking Phase'}
              color={session.current_phase === 'prep' ? 'secondary' : 'primary'}
              variant="filled"
            />
            <Chip
              label={session.is_active ? 'Active' : 'Paused'}
              color={session.is_active ? 'success' : 'warning'}
              variant="outlined"
            />
          </Box>
        </Box>

        {/* Current Step */}
        <motion.div
          key={session.current_step}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Card sx={{ mb: 4 }}>
            <CardContent sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h5" component="h2" gutterBottom>
                Current Step
              </Typography>
              <Typography variant="h4" sx={{ mb: 3, minHeight: 60 }}>
                {session.current_step}
              </Typography>
              
              {/* Timer Component - shows when minutes are detected in the instruction */}
              <Timer 
                key={session.current_step}
                instruction={session.current_step}
                autoStart={shouldStartTimer && timestamp > 0}
                shouldPause={shouldPauseTimer}
                shouldResume={shouldResumeTimer}
                onComplete={() => {
                  // Optional: Auto-advance to next step when timer completes
                  // sendVoiceCommand('next');
                  setShouldStartTimer(false); // Reset after completion
                  setShouldPauseTimer(false);
                  setShouldResumeTimer(false);
                  setTimestamp(0); // Reset timestamp
                }}
              />
              
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  startIcon={<NextIcon />}
                  onClick={() => sendVoiceCommand('next')}
                  disabled={loading}
                >
                  Next Step
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<RepeatIcon />}
                  onClick={() => sendVoiceCommand('repeat')}
                  disabled={loading}
                >
                  Repeat
                </Button>
              </Box>
            </CardContent>
          </Card>
        </motion.div>

        {/* Voice Response */}
        {/*
        <AnimatePresence>
          {lastResponse && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <Alert severity="info" sx={{ mb: 4 }}>
                {lastResponse}
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>
        */}

        {/* New Recipe Created Notification */}
        <AnimatePresence>
          {newRecipeCreated && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <Alert 
                severity="success" 
                sx={{ mb: 4 }}
                action={
                  <Button
                    color="inherit"
                    size="small"
                    onClick={() => {
                      window.open(`/recipes`, '_blank');
                      setNewRecipeCreated(null);
                    }}
                  >
                    View Recipe
                  </Button>
                }
              >
                <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                  New Recipe Created!
                </Typography>
                <Typography variant="body2">
                  "{newRecipeCreated.title}" has been saved to your recipe library.
                </Typography>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Wake Word Status Indicator */}
        {!listening && isWakeWordMode && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Alert severity="info" sx={{ mb: 4, opacity: 0.7 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MicIcon />
                <Typography variant="body2">
                  Voice assistant starting up... Say "Hey Prep" to activate.
                </Typography>
              </Box>
            </Alert>
          </motion.div>
        )}

        {/* Speech Recognition Status */}
        <AnimatePresence>
          {listening && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              <Alert severity={isWakeWordMode ? "info" : "success"} sx={{ mb: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <MicIcon sx={{ animation: 'pulse 1.5s infinite' }} />
                  <Typography>
                    {isWakeWordMode ? (
                      <>
                        Listening for "Hey Prep"...
                        <Typography variant="caption" display="block" sx={{ opacity: 0.8 }}>
                          Say "Hey Prep" to activate voice commands
                        </Typography>
                      </>
                    ) : (
                      <>
                        Listening for command... {voiceCommand && `"${voiceCommand}"`}
                        <Typography variant="caption" display="block" sx={{ opacity: 0.8 }}>
                          Will stop automatically after 5 seconds of silence
                        </Typography>
                      </>
                    )}
                  </Typography>
                </Box>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Quick Commands */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Quick Commands
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
              {quickCommands.map((cmd, index) => (
                <Box key={index} sx={{ flex: '1 1 calc(50% - 8px)', minWidth: 120 }}>
                  <motion.div
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Button
                      fullWidth
                      variant="outlined"
                      startIcon={cmd.icon}
                      onClick={() => sendVoiceCommand(cmd.command)}
                      disabled={loading}
                      sx={{ py: 1.5 }}
                    >
                      {cmd.label}
                    </Button>
                  </motion.div>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>


        {/* Floating Action Button */}
        <Fab
          color={isWakeWordMode ? "primary" : (listening ? "secondary" : "default")}
          aria-label="voice command"
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
            animation: listening ? 'pulse 1.5s infinite' : 'none',
          }}
          onClick={toggleSpeechRecognition}
        >
          <MicIcon />
        </Fab>
      </motion.div>
    </Container>
  );
};

export default CookingSession;

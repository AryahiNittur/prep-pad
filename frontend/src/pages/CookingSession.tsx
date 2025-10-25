import React, { useState, useEffect } from 'react';
import { useSpeechSynthesis } from 'react-speech-kit';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Chip,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import {
  SkipNext as NextIcon,
  Replay as RepeatIcon,
  Mic as MicIcon,
  Kitchen as KitchenIcon,
  Timer as TimerIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

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
  const navigate = useNavigate();
  const [session, setSession] = useState<SessionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [voiceDialogOpen, setVoiceDialogOpen] = useState(false);
  const [voiceCommand, setVoiceCommand] = useState('');
  const [lastResponse, setLastResponse] = useState<string | null>(null);

  const { speak, voices } = useSpeechSynthesis();

  useEffect(() => {
    if (sessionId) {
      fetchSession();
    }
  }, [sessionId]);

  const fetchSession = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/cooking_session/${sessionId}`);
      setSession(response.data);
    } catch (error) {
      console.error('Failed to fetch session:', error);
    }
  };

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
      
      // Update session if provided
      if (voiceResponse.current_step) {
        setSession(prev => prev ? {
          ...prev,
          current_step: voiceResponse.current_step!,
          current_phase: voiceResponse.current_phase || prev.current_phase,
          is_active: !voiceResponse.is_complete,
        } : null);
      }

      speak({ text: voiceResponse.response, voice:  voices[4] });

      // Close dialog if command was processed
      setVoiceDialogOpen(false);
      setVoiceCommand('');
    } catch (error) {
      console.error('Failed to send voice command:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickCommands = [
    { command: 'next', label: 'Next Step', icon: <NextIcon /> },
    { command: 'repeat', label: 'Repeat', icon: <RepeatIcon /> },
    { command: 'what prep', label: 'What Prep?', icon: <KitchenIcon /> },
    { command: 'time', label: 'Time Left', icon: <TimerIcon /> },
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

        {/* Voice Input Dialog */}
        <Dialog
          open={voiceDialogOpen}
          onClose={() => setVoiceDialogOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Voice Command</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Command"
              fullWidth
              variant="outlined"
              value={voiceCommand}
              onChange={(e) => setVoiceCommand(e.target.value)}
              placeholder="e.g., 'next', 'repeat', 'what prep', 'pause'"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setVoiceDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={() => sendVoiceCommand(voiceCommand)}
              variant="contained"
              disabled={loading || !voiceCommand.trim()}
            >
              Send Command
            </Button>
          </DialogActions>
        </Dialog>

        {/* Floating Action Button */}
        <Fab
          color="primary"
          aria-label="voice command"
          sx={{
            position: 'fixed',
            bottom: 16,
            right: 16,
          }}
          onClick={() => setVoiceDialogOpen(true)}
        >
          <MicIcon />
        </Fab>
      </motion.div>
    </Container>
  );
};

export default CookingSession;

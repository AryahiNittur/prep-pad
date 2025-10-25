import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Paper,
} from '@mui/material';
import {
  Restaurant as RestaurantIcon,
  Kitchen as KitchenIcon,
  VoiceOverOff as VoiceIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { TypeAnimation } from 'react-type-animation';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <RestaurantIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Recipe Parsing',
      description: 'Paste any recipe URL and get an AI-optimized prep workflow',
    },
    {
      icon: <KitchenIcon sx={{ fontSize: 40, color: 'secondary.main' }} />,
      title: 'Prep-First Workflow',
      description: 'Organize ingredients and prep tasks before cooking starts',
    },
    {
      icon: <VoiceIcon sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'Voice Control',
      description: 'Hands-free cooking with voice commands like "Next" and "Repeat"',
    },
    {
      icon: <SpeedIcon sx={{ fontSize: 40, color: 'secondary.main' }} />,
      title: 'Parallel Tasks',
      description: 'Identify what can be done simultaneously to save time',
    },
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        <Box textAlign="center" mb={6}>
          <Typography
            variant="h2"
            component="h1"
            gutterBottom
            sx={{ fontWeight: 700, mb: 2 }}
          >
            Welcome to{' '}
            <TypeAnimation
              cursor={true}
              sequence={[
                'Prep Pad',
                2000,
                'Your Cooking Assistant',
                2000,
                'AI Recipe Optimizer',
                2000,
              ]}
              wrapper="span"
              repeat={Infinity}
              style={{ color: '#ff6b35' }}
            />
          </Typography>
          
          <Typography
            variant="h5"
            color="text.secondary"
            sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}
          >
            Transform any messy recipe blog into a clean, efficient cooking workflow
            with AI-powered optimization and voice-controlled guidance.
          </Typography>

          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/parse')}
              sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
            >
              Start Cooking
            </Button>
          </motion.div>
        </Box>
      </motion.div>

      {/* Features Section */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <Typography variant="h3" component="h2" textAlign="center" gutterBottom sx={{ mb: 4 }}>
          How It Works
        </Typography>
        
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4, mb: 6 }}>
          {features.map((feature, index) => (
            <Box key={index} sx={{ flex: '1 1 calc(50% - 16px)', minWidth: 300 }}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -5 }}
              >
                <Card
                  sx={{
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: 6,
                    },
                  }}
                >
                  <CardContent sx={{ flexGrow: 1, textAlign: 'center', p: 3 }}>
                    <Box mb={2}>{feature.icon}</Box>
                    <Typography variant="h5" component="h3" gutterBottom>
                      {feature.title}
                    </Typography>
                    <Typography color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </motion.div>
            </Box>
          ))}
        </Box>
      </motion.div>

      {/* CTA Section */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.4 }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            background: 'linear-gradient(135deg, #ff6b35 0%, #f7931e 100%)',
            color: 'white',
          }}
        >
          <Typography variant="h4" component="h2" gutterBottom>
            Ready to Cook Smarter?
          </Typography>
          <Typography variant="h6" sx={{ mb: 3, opacity: 0.9 }}>
            Paste a recipe URL and let AI optimize your cooking workflow
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/parse')}
            sx={{
              backgroundColor: 'white',
              color: 'primary.main',
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
              '&:hover': {
                backgroundColor: 'rgba(255,255,255,0.9)',
              },
            }}
          >
            Parse Your First Recipe
          </Button>
        </Paper>
      </motion.div>
    </Container>
  );
};

export default Home;

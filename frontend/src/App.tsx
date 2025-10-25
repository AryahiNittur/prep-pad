import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';
import { motion } from 'framer-motion';

// Components
import Navbar from './components/Navbar';
import Home from './pages/Home';
import RecipeParser from './pages/RecipeParser';
import CookingSession from './pages/CookingSession';
import RecipeLibrary from './pages/RecipeLibrary';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#ff6b35', // Orange for cooking theme
      light: '#ff8a65',
      dark: '#e64a19',
    },
    secondary: {
      main: '#4caf50', // Green for success/ready
      light: '#81c784',
      dark: '#388e3c',
    },
    background: {
      default: '#fafafa',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 600,
    },
    h2: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navbar />
          <motion.main
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            style={{ flex: 1 }}
          >
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/parse" element={<RecipeParser />} />
              <Route path="/cooking/:sessionId" element={<CookingSession />} />
              <Route path="/recipes" element={<RecipeLibrary />} />
            </Routes>
          </motion.main>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;
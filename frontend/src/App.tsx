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
      main: '#f59e0b', // Amber-500
      light: '#fbbf24', // Amber-400
      dark: '#d97706', // Amber-600
    },
    secondary: {
      main: '#f97316', // Orange-500
      light: '#fb923c', // Orange-400
      dark: '#ea580c', // Orange-600
    },
    background: {
      default: '#fffbeb', // Amber-50
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
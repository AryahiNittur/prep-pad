import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Chip,
  Button,
  CircularProgress,
  Alert,
  CardActions,
} from '@mui/material';
import {
  Restaurant as RestaurantIcon,
  AccessTime as TimeIcon,
  People as PeopleIcon,
  PlayArrow as PlayIcon,
  Delete as DeleteIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface Recipe {
  id: number;
  title: string;
  source_url: string;
  total_time?: number;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
  difficulty?: string;
  created_at: string;
}

const RecipeLibrary: React.FC = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    fetchRecipes();
    checkFavorites();
  }, []);

  const fetchRecipes = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/recipes');
      setRecipes(response.data.recipes);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch recipes');
    } finally {
      setLoading(false);
    }
  };

  const startCooking = async (recipeId: number) => {
    try {
      const response = await axios.post(`http://localhost:8000/api/start_cooking/${recipeId}`);
      navigate(`/cooking/${response.data.session_id}`);
    } catch (err) {
      console.error('Failed to start cooking session:', err);
    }
  };

  const deleteRecipe = async (recipeId: number) => {
    try {
      await axios.delete(`http://localhost:8000/api/recipe/${recipeId}`);
      setRecipes(recipes.filter(recipe => recipe.id !== recipeId));  // This line removes it
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete recipe');
    }
  };

  const checkFavorites = async () => {
    try {
      const favoriteRecipes = await axios.get('http://localhost:8000/api/favorites');
      const favoriteIds = new Set<number>(favoriteRecipes.data.recipes.map((recipe: Recipe) => recipe.id));
      setFavorites(favoriteIds);
    } catch (err) {
      console.error('Failed to check favorites:', err);
    }
  };

  const toggleFavorite = async (recipeId: number) => {
    try {
      if (favorites.has(recipeId)) {
        await axios.delete(`http://localhost:8000/api/favorites/${recipeId}`);
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(recipeId);
          return newSet;
        });
      } else {
        await axios.post(`http://localhost:8000/api/favorites/${recipeId}`);
        setFavorites(prev => new Set(prev).add(recipeId));
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update favorites');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          backgroundImage: 'url("/preppadhomepagephoto.jpg")',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundAttachment: 'fixed',
          position: 'relative',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(255, 255, 255, 0.85)',
            zIndex: 1,
          },
        }}
      >
        <Container maxWidth="lg" sx={{ py: 4, position: 'relative', zIndex: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        </Container>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundImage: 'url("/preppadhomepagephoto.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundAttachment: 'fixed',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(255, 255, 255, 0.85)',
          zIndex: 1,
        },
      }}
    >
      <Container maxWidth="lg" sx={{ py: 4, position: 'relative', zIndex: 2 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Typography variant="h3" component="h1" gutterBottom>
          Recipe Library
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
          Your saved recipes ready for cooking
        </Typography>
      </motion.div>

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {recipes.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 6 }}>
              <RestaurantIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                No Recipes Yet
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                Parse your first recipe to get started!
              </Typography>
              <Button
                variant="contained"
                onClick={() => navigate('/parse')}
                startIcon={<RestaurantIcon />}
              >
                Parse Recipe
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      ) : (
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {recipes.map((recipe, index) => (
            <Box key={recipe.id} sx={{ flex: '1 1 calc(33.333% - 16px)', minWidth: 280 }}>
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
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" component="h2" gutterBottom>
                      {recipe.title}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                      {recipe.total_time && (
                        <Chip
                          icon={<TimeIcon />}
                          label={`${recipe.total_time} min`}
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}
                      {recipe.servings && (
                        <Chip
                          icon={<PeopleIcon />}
                          label={`${recipe.servings} servings`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                      {recipe.difficulty && (
                        <Chip
                          label={recipe.difficulty}
                          size="small"
                          color="secondary"
                          variant="outlined"
                        />
                      )}
                    </Box>

                    <Typography variant="body2" color="text.secondary">
                      Added {formatDate(recipe.created_at)}
                    </Typography>
                  </CardContent>
                  
                  <CardActions>
                    <Button
                      variant="contained"
                      startIcon={<PlayIcon />}
                      onClick={() => startCooking(recipe.id)}
                      fullWidth
                    >
                      Start Cooking
                    </Button>
                    <Button
                      variant="outlined"
                      color={favorites.has(recipe.id) ? "error" : "inherit"}
                      onClick={() => toggleFavorite(recipe.id)}
                      sx={{ minWidth: 'auto' }}
                    >
                      {favorites.has(recipe.id) ? <FavoriteIcon /> : <FavoriteBorderIcon />}
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={() => deleteRecipe(recipe.id)}
                      sx={{ minWidth: 'auto' }}
                    >
                      <DeleteIcon />
                    </Button>
                  </CardActions>
                </Card>
              </motion.div>
            </Box>
          ))}
        </Box>
      )}
      </Container>
    </Box>
  );
};

export default RecipeLibrary;

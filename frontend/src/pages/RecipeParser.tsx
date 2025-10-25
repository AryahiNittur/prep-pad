import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  Divider,
  Paper,
} from '@mui/material';
import {
  Send as SendIcon,
  Restaurant as RestaurantIcon,
  AccessTime as TimeIcon,
  People as PeopleIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useFormik } from 'formik';
import * as yup from 'yup';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

interface Ingredient {
  name: string;
  amount?: string;
  unit?: string;
  notes?: string;
}

interface PrepStep {
  instruction: string;
  time_estimate?: number;
  category?: string;
}

interface CookStep {
  step_number: number;
  instruction: string;
  time_estimate?: number;
  parallel_tasks?: string[];
}

interface OptimizedRecipe {
  title: string;
  ingredients: Ingredient[];
  prep_phase: PrepStep[];
  cook_phase: CookStep[];
  total_time?: number;
  prep_time?: number;
  cook_time?: number;
  servings?: number;
  difficulty?: string;
}

const validationSchema = yup.object({
  url: yup
    .string()
    .url('Please enter a valid URL')
    .required('Recipe URL is required'),
});

const RecipeParser: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [recipe, setRecipe] = useState<OptimizedRecipe | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const formik = useFormik({
    initialValues: {
      url: '',
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      setLoading(true);
      setError(null);
      setRecipe(null);

      try {
        const response = await axios.post('http://localhost:8000/api/parse_recipe', {
          url: values.url,
        });

        setRecipe(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to parse recipe');
      } finally {
        setLoading(false);
      }
    },
  });

  const startCooking = async () => {
    if (!recipe) return;

    try {
      const response = await axios.post('http://localhost:8000/api/start_cooking/1');
      navigate(`/cooking/${response.data.session_id}`);
    } catch (err) {
      console.error('Failed to start cooking session:', err);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Typography variant="h3" component="h1" gutterBottom textAlign="center">
          Parse Recipe
        </Typography>
        <Typography variant="h6" color="text.secondary" textAlign="center" sx={{ mb: 4 }}>
          Paste any recipe URL and get an AI-optimized cooking workflow
        </Typography>
      </motion.div>

      {/* URL Input Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <form onSubmit={formik.handleSubmit}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                <TextField
                  fullWidth
                  id="url"
                  name="url"
                  label="Recipe URL"
                  placeholder="https://www.allrecipes.com/recipe/..."
                  value={formik.values.url}
                  onChange={formik.handleChange}
                  error={formik.touched.url && Boolean(formik.errors.url)}
                  helperText={formik.touched.url && formik.errors.url}
                  disabled={loading}
                />
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading || !formik.isValid}
                  startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
                  sx={{ minWidth: 120 }}
                >
                  {loading ? 'Parsing...' : 'Parse'}
                </Button>
              </Box>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Alert severity="error" sx={{ mb: 4 }}>
              {error}
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Recipe Display */}
      <AnimatePresence>
        {recipe && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.6 }}
          >
            <Card>
              <CardContent>
                {/* Recipe Header */}
                <Box sx={{ mb: 4 }}>
                  <Typography variant="h4" component="h2" gutterBottom>
                    {recipe.title}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                    {recipe.total_time && (
                      <Chip
                        icon={<TimeIcon />}
                        label={`${recipe.total_time} min total`}
                        color="primary"
                        variant="outlined"
                      />
                    )}
                    {recipe.prep_time && (
                      <Chip
                        label={`${recipe.prep_time} min prep`}
                        color="secondary"
                        variant="outlined"
                      />
                    )}
                    {recipe.servings && (
                      <Chip
                        icon={<PeopleIcon />}
                        label={`${recipe.servings} servings`}
                        variant="outlined"
                      />
                    )}
                    {recipe.difficulty && (
                      <Chip
                        label={recipe.difficulty}
                        color="default"
                        variant="outlined"
                      />
                    )}
                  </Box>

                  <Button
                    variant="contained"
                    size="large"
                    onClick={startCooking}
                    startIcon={<RestaurantIcon />}
                    sx={{ mb: 3 }}
                  >
                    Start Cooking
                  </Button>
                </Box>

                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {/* Ingredients */}
                    <Box sx={{ flex: '1 1 calc(50% - 16px)', minWidth: 300 }}>
                      <Paper sx={{ p: 3 }}>
                        <Typography variant="h5" component="h3" gutterBottom>
                          Ingredients
                        </Typography>
                        <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
                          {recipe.ingredients.map((ingredient, index) => (
                            <Box key={index} sx={{ mb: 1 }}>
                              <Typography variant="body2">
                                <strong>{ingredient.amount} {ingredient.unit}</strong> {ingredient.name}
                                {ingredient.notes && (
                                  <Typography component="span" color="text.secondary" sx={{ ml: 1 }}>
                                    ({ingredient.notes})
                                  </Typography>
                                )}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </Paper>
                    </Box>

                    {/* Prep Phase */}
                    <Box sx={{ flex: '1 1 calc(50% - 16px)', minWidth: 300 }}>
                      <Paper sx={{ p: 3 }}>
                        <Typography variant="h5" component="h3" gutterBottom>
                          Prep Phase
                        </Typography>
                        <Box sx={{ maxHeight: 300, overflowY: 'auto' }}>
                          {recipe.prep_phase.map((step, index) => (
                            <Box key={index} sx={{ mb: 2 }}>
                              <Typography variant="body2">
                                {step.instruction}
                                {step.time_estimate && (
                                  <Chip
                                    label={`${step.time_estimate} min`}
                                    size="small"
                                    sx={{ ml: 1 }}
                                  />
                                )}
                              </Typography>
                              {step.category && (
                                <Chip
                                  label={step.category}
                                  size="small"
                                  color="secondary"
                                  sx={{ mt: 0.5 }}
                                />
                              )}
                            </Box>
                          ))}
                        </Box>
                      </Paper>
                    </Box>
                  </Box>

                  {/* Cook Phase */}
                  <Box>
                    <Paper sx={{ p: 3 }}>
                      <Typography variant="h5" component="h3" gutterBottom>
                        Cooking Phase
                      </Typography>
                      <Box sx={{ maxHeight: 400, overflowY: 'auto' }}>
                        {recipe.cook_phase.map((step, index) => (
                          <Box key={index} sx={{ mb: 2 }}>
                            <Typography variant="body1" sx={{ mb: 1 }}>
                              <strong>Step {step.step_number}:</strong> {step.instruction}
                              {step.time_estimate && (
                                <Chip
                                  label={`${step.time_estimate} min`}
                                  size="small"
                                  sx={{ ml: 1 }}
                                />
                              )}
                            </Typography>
                            {step.parallel_tasks && step.parallel_tasks.length > 0 && (
                              <Box sx={{ ml: 2 }}>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                  While doing this, you can also:
                                </Typography>
                                {step.parallel_tasks.map((task, taskIndex) => (
                                  <Typography key={taskIndex} variant="body2" sx={{ ml: 1 }}>
                                    • {task}
                                  </Typography>
                                ))}
                              </Box>
                            )}
                            {index < recipe.cook_phase.length - 1 && <Divider sx={{ mt: 2 }} />}
                          </Box>
                        ))}
                      </Box>
                    </Paper>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </Container>
  );
};

export default RecipeParser;

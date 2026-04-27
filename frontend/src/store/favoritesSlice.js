import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import userService from '../services/userService'

const getErrorMessage = (err, fallback) =>
  err.response?.data?.detail || err.response?.data?.message || err.message || fallback

export const fetchFavoritesThunk = createAsyncThunk('favorites/fetchAll', async (_, thunkAPI) => {
  try {
    return await userService.getFavorites()
  } catch (err) {
    return thunkAPI.rejectWithValue(getErrorMessage(err, 'Failed to fetch favorites'))
  }
})

export const addFavoriteThunk = createAsyncThunk('favorites/add', async (restaurantId, thunkAPI) => {
  try {
    return await userService.addFavorite(restaurantId)
  } catch (err) {
    return thunkAPI.rejectWithValue(getErrorMessage(err, 'Failed to add favorite'))
  }
})

export const removeFavoriteThunk = createAsyncThunk('favorites/remove', async (favoriteId, thunkAPI) => {
  try {
    return await userService.removeFavorite(favoriteId)
  } catch (err) {
    return thunkAPI.rejectWithValue(getErrorMessage(err, 'Failed to remove favorite'))
  }
})

const favoritesSlice = createSlice({
  name: 'favorites',
  initialState: {
    favorites: [],
    loading: false,
    error: null
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchFavoritesThunk.pending, (state) => { state.loading = true })
      .addCase(fetchFavoritesThunk.fulfilled, (state, action) => {
        state.loading = false
        state.favorites = action.payload
      })
      .addCase(fetchFavoritesThunk.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      .addCase(addFavoriteThunk.fulfilled, (state, action) => {
        state.favorites.push(action.payload)
      })
      .addCase(removeFavoriteThunk.fulfilled, (state, action) => {
        state.favorites = state.favorites.filter(f => f.id !== action.meta.arg)
      })
  }
})

export default favoritesSlice.reducer 

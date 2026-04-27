import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import restaurantService from '../services/restaurantService'

const getErrorMessage = (err, fallback) =>
  err.response?.data?.detail || err.response?.data?.message || err.message || fallback

export const fetchRestaurantsThunk = createAsyncThunk('restaurant/fetchAll', async (filters, thunkAPI) => {
  try {
    return await restaurantService.searchRestaurants(filters)
  } catch (err) {
    return thunkAPI.rejectWithValue(getErrorMessage(err, 'Failed to fetch restaurants'))
  }
})

export const fetchRestaurantByIdThunk = createAsyncThunk('restaurant/fetchById', async (id, thunkAPI) => {
  try {
    return await restaurantService.getRestaurant(id)
  } catch (err) {
    return thunkAPI.rejectWithValue(getErrorMessage(err, 'Failed to fetch restaurant'))
  }
})

const restaurantSlice = createSlice({
  name: 'restaurant',
  initialState: {
    restaurants: [],
    selectedRestaurant: null,
    loading: false,
    error: null,
    filters: {}
  },
  reducers: {
    setFilters(state, action) {
      state.filters = action.payload
    },
    clearSelectedRestaurant(state) {
      state.selectedRestaurant = null
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurantsThunk.pending, (state) => { state.loading = true; state.error = null })
      .addCase(fetchRestaurantsThunk.fulfilled, (state, action) => {
        state.loading = false
        state.restaurants = action.payload
      })
      .addCase(fetchRestaurantsThunk.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      .addCase(fetchRestaurantByIdThunk.pending, (state) => { state.loading = true; state.error = null })
      .addCase(fetchRestaurantByIdThunk.fulfilled, (state, action) => {
        state.loading = false
        state.selectedRestaurant = action.payload
      })
      .addCase(fetchRestaurantByIdThunk.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
  }
})

export const { setFilters, clearSelectedRestaurant } = restaurantSlice.actions
export default restaurantSlice.reducer 

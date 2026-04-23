import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import restaurantService from '../services/restaurantService'

export const fetchRestaurantsThunk = createAsyncThunk('restaurant/fetchAll', async (filters, thunkAPI) => {
  try {
    return await restaurantService.search(filters)
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Failed to fetch restaurants')
  }
})

export const fetchRestaurantByIdThunk = createAsyncThunk('restaurant/fetchById', async (id, thunkAPI) => {
  try {
    return await restaurantService.get(id)
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Failed to fetch restaurant')
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

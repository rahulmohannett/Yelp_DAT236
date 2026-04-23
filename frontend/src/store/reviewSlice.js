import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import reviewService from '../services/reviewService'

export const fetchReviewsThunk = createAsyncThunk('review/fetchAll', async (restaurantId, thunkAPI) => {
  try {
    return await reviewService.getReviews(restaurantId)
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Failed to fetch reviews')
  }
})

export const createReviewThunk = createAsyncThunk('review/create', async ({ restaurantId, reviewData }, thunkAPI) => {
  try {
    return await reviewService.createReview(restaurantId, reviewData)
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Failed to submit review')
  }
})

export const updateReviewThunk = createAsyncThunk('review/update', async ({ reviewId, data }, thunkAPI) => {
  try {
    return await reviewService.updateReview(reviewId, data)
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Failed to update review')
  }
})

export const deleteReviewThunk = createAsyncThunk('review/delete', async (reviewId, thunkAPI) => {
  try {
    return await reviewService.deleteReview(reviewId)
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Failed to delete review')
  }
})

const reviewSlice = createSlice({
  name: 'review',
  initialState: {
    reviews: [],
    loading: false,
    error: null,
    submitStatus: null
  },
  reducers: {
    clearSubmitStatus(state) {
      state.submitStatus = null
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchReviewsThunk.pending, (state) => { state.loading = true; state.error = null })
      .addCase(fetchReviewsThunk.fulfilled, (state, action) => {
        state.loading = false
        state.reviews = action.payload
      })
      .addCase(fetchReviewsThunk.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      .addCase(createReviewThunk.pending, (state) => { state.submitStatus = 'pending' })
      .addCase(createReviewThunk.fulfilled, (state) => { state.submitStatus = 'success' })
      .addCase(createReviewThunk.rejected, (state) => { state.submitStatus = 'error' })
      .addCase(updateReviewThunk.pending, (state) => { state.submitStatus = 'pending' })
      .addCase(updateReviewThunk.fulfilled, (state) => { state.submitStatus = 'success' })
      .addCase(updateReviewThunk.rejected, (state) => { state.submitStatus = 'error' })
      .addCase(deleteReviewThunk.pending, (state) => { state.submitStatus = 'pending' })
      .addCase(deleteReviewThunk.fulfilled, (state) => { state.submitStatus = 'success' })
      .addCase(deleteReviewThunk.rejected, (state) => { state.submitStatus = 'error' })
  }
})

export const { clearSubmitStatus } = reviewSlice.actions
export default reviewSlice.reducer 

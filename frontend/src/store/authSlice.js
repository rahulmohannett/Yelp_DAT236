import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import authService from '../services/authService'

export const loginThunk = createAsyncThunk('auth/login', async (credentials, thunkAPI) => {
  try {
    const data = await authService.login(credentials)
    localStorage.setItem('token', data.token)
    return data
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Login failed')
  }
})

export const registerThunk = createAsyncThunk('auth/register', async (userData, thunkAPI) => {
  try {
    const data = await authService.register(userData)
    localStorage.setItem('token', data.token)
    return data
  } catch (err) {
    return thunkAPI.rejectWithValue(err.response?.data?.message || 'Register failed')
  }
})

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    token: localStorage.getItem('token') || null,
    user: null,
    isAuthenticated: !!localStorage.getItem('token'),
    loading: false,
    error: null
  },
  reducers: {
    logoutAction(state) {
      state.token = null
      state.user = null
      state.isAuthenticated = false
      localStorage.removeItem('token')
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginThunk.pending, (state) => { state.loading = true; state.error = null })
      .addCase(loginThunk.fulfilled, (state, action) => {
        state.loading = false
        state.token = action.payload.token
        state.user = action.payload.user
        state.isAuthenticated = true
      })
      .addCase(loginThunk.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
      .addCase(registerThunk.pending, (state) => { state.loading = true; state.error = null })
      .addCase(registerThunk.fulfilled, (state, action) => {
        state.loading = false
        state.token = action.payload.token
        state.user = action.payload.user
        state.isAuthenticated = true
      })
      .addCase(registerThunk.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload
      })
  }
})

export const { logoutAction } = authSlice.actions
export default authSlice.reducer 

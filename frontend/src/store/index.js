import { configureStore } from '@reduxjs/toolkit'
import authReducer from './authSlice'
import restaurantReducer from './restaurantSlice'
import reviewReducer from './reviewSlice'
import favoritesReducer from './favoritesSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    restaurant: restaurantReducer,
    review: reviewReducer,
    favorites: favoritesReducer
  }
}) 

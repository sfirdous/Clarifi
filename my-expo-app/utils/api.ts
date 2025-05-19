import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';


const API_BASE_URL = 'https://6771-2401-4900-acb5-795e-38d7-d333-b439-bc82.ngrok-free.app';  
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // Set timeout to 10 seconds

});

export const getStats = async () => {
  const pdf_id = await AsyncStorage.getItem('pdf_id');
  const user_id = await AsyncStorage.getItem('user_id');
  if (!pdf_id || !user_id) throw new Error('Missing user_id or pdf_id');

  const response = await axios.get(`${API_BASE_URL}/stats/${pdf_id}`, {
    params: { user_id },
  });
  return response.data;
};

export const getWeeklyTrends = async () => {
  const pdf_id = await AsyncStorage.getItem('pdf_id');
  const user_id = await AsyncStorage.getItem('user_id');
  if (!pdf_id || !user_id) throw new Error('Missing user_id or pdf_id');

  const response = await axios.get(`${API_BASE_URL}/weekly-trends/${pdf_id}`, {
    params: { user_id },
  });
  return response.data;
};

export default api;

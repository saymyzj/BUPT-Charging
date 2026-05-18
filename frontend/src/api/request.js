import axios from 'axios';
import { getAuthToken } from '@/utils/authSession'

const service = axios.create({
  baseURL: '',
  timeout: 10000,
});

service.interceptors.request.use(
  (config) => {
    const token = getAuthToken()
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
);

service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('接口请求异常:', error);
    return Promise.reject(error);
  }
);

export function unwrapResponseData(res) {
  if (res && typeof res === 'object' && 'code' in res) {
    return res.code === 0 ? (res.data ?? {}) : res
  }
  return res
}

export default service;

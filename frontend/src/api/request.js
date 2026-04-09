import axios from 'axios';

const service = axios.create({
  baseURL: '',
  timeout: 10000,
});

service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
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

export default service;

import axios from 'axios';

const service = axios.create({
  baseURL: '',
  timeout: 10000,
});

service.interceptors.request.use(
  (config) => config,
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

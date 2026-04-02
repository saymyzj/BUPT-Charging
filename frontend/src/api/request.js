import axios from 'axios';

// 创建 axios 实例
const service = axios.create({
  // 把 baseURL 改回走当前域名的 /api，交给 Vite 的本地代理去做转发和擦除前缀
  baseURL: '/api', 
  timeout: 10000,   // 超时时间
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    return config;
  },
// ...existing code...
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    // 假设后端统一格式为 { code: 0, message: "ok", data: {...} }
    const res = response.data;
    // 这里可以统一做错误码处理工作！避免到处写 if-else
    return res;
  },
  (error) => {
    console.error('接口请求异常:', error);
    return Promise.reject(error);
  }
);

export default service;

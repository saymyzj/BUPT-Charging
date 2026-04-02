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
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    // 假设后端统一格式为 { code: 0, message: "ok", data: {...} }
    const res = response.data;
    // 直接返回 response.data，与冻结接口文档_前端实现版保持一致
    return res;
  },
  (error) => {
    // 统一弹窗处理机制，保留原 console.error 以防无 ElementPlus 上下文报错
    console.error('接口请求异常:', error);
    const errMessage = error.response && error.response.data && error.response.data.message ? error.response.data.message : '请求失败';
    console.error(errMessage);
    return Promise.reject(error);
  }
);

export default service;
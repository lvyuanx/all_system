// request.js
(function (global) {
  if (!global.axios) {
    throw new Error('请先引入 axios');
  }
  if (!global.SimpleUIExtra || !global.SimpleUIExtra.ElMessage || !global.SimpleUIExtra.ElMessageBox) {
    throw new Error('请先引入SimpleUIExtra');
  }

  const { ElMessage, ElMessageBox } = global.SimpleUIExtra;  // 引入父页面的组件

  const TOKEN_TAG = 'X-Authorization';
  const TOKEN_ORIGIN = 'cookie'; // token 来源，可改为 'header'

  const token_set_handle_map = {
    cookie: null, // 从 cookie 取，不加 header
    header: (config, token) => {
      config.headers[TOKEN_TAG] = `Bearer ${token}`;
    },
  };

  // 创建 axios 实例
  const service = axios.create({
    baseURL: '/api',
    timeout: 15000,
    headers: {
      'Content-Type': 'application/json', // 默认 JSON
    },
  });

  // 请求拦截器
  service.interceptors.request.use(
    config => {
      const token = localStorage.getItem(TOKEN_TAG);
      const setToken = token_set_handle_map[TOKEN_ORIGIN];
      setToken && setToken(config, token);
      console.log('[Request]', config.method.toUpperCase(), config.url);
      return config;
    },
    error => Promise.reject(error)
  );

  // 响应拦截器
  service.interceptors.response.use(
    response => {
      const res = response.data;

      // 没有 code 字段，直接返回
      if (typeof res.code === 'undefined') {
        return res;
      }

      if (res.code != 0) {
        const msg = res.msg || '请求错误';
        const level = res.level || "e"
        if (level === "e") {
            ElMessageBox.alert(
                msg, 
                `错误:${res.code}`, 
                {
                    confirmButtonText: "确定",
                    type: "error"
                }
            )
        } else if (level === "w") {
            ElMessage.warning(msg);
        } else {
            ElMessage.info(msg);
        }
        console.error('[Business Error]', res);
        throw new Error(msg);
      }

      return res.data; // 直接返回 data
    },
    error => {
      console.error('[Response Error]', error);
      ElMessageBox.alert(
            "服务器异常，请稍后再试！", 
            "错误", 
            {
                confirmButtonText: "确定",
                type: "error"
            }
        )
      return Promise.reject(error);
    }
  );

  // 封装异步方法
  global.request = {
    async get(url, params = {}, config = {}) {
      return service({ method: 'get', url, params, ...config });
    },
    async post(url, data = {}, params = {}, config = {}) {
      return service({ method: 'post', url, data, params, ...config });
    },
    async put(url, data = {}, params = {}, config = {}) {
      return service({ method: 'put', url, data, params, ...config });
    },
    async delete(url, data = {}, params = {}, config = {}) {
      return service({ method: 'delete', url, data, params, ...config });
    }
  };

})(window);

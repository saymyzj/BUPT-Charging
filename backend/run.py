from app import create_app

app = create_app('development')

if __name__ == '__main__':
    # 监听0.0.0.0，支持跨设备访问
    # port=8080 为统一接口文档规定的端口
    app.run(host='0.0.0.0', port=8080, debug=True)

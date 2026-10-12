// 后端 API 封装
// 真机调试：把 BASE_URL 改为电脑局域网 IP，例如 http://192.168.1.5:5000/api
// 注意：手机与电脑需在同一网络；微信开发者工具需关闭域名校验；真机预览需开启「开发调试」
let BASE_URL = 'http://127.0.0.1:5000/api'

// 清洗剪贴板粘贴可能带入的零宽字符/反引号，避免请求失败
BASE_URL = BASE_URL.replace(/[\u200b-\u200f\u2028\u2029\uFEFF`]/g, '').trim()

function getOpenid() {
  return wx.getStorageSync('openid') || ''
}

// 统一请求：resolve 业务成功数据；reject Error(msg) 并 toast 提示
function request(method, path, data, silent) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + path,
      method: method,
      data: data || {},
      header: {
        'Content-Type': 'application/json',
        'X-OpenID': getOpenid(),
      },
      success(res) {
        const body = res.data || {}
        if (res.statusCode >= 200 && res.statusCode < 300 && body.code === 0) {
          resolve(body)
        } else {
          const msg = body.msg || ('Request failed (' + res.statusCode + ')')
          if (!silent) wx.showToast({ title: msg, icon: 'none', duration: 2500 })
          reject(new Error(msg))
        }
      },
      fail() {
        const msg = 'Network error: make sure the backend is running and on the same network'
        if (!silent) wx.showToast({ title: msg, icon: 'none', duration: 3000 })
        reject(new Error(msg))
      },
    })
  })
}

module.exports = {
  BASE_URL,
  get: (path, silent) => request('GET', path, null, silent),
  post: (path, data, silent) => request('POST', path, data, silent),
}

const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    authStatus: 'none', // none / pending / approved / rejected
    authReason: '',
    submitting: false,
  },

  onShow() {
    app.ensureUser(() => this.loadStatus())
  },

  loadStatus() {
    api.get('/user/auth/status').then(res => {
      this.setData({ authStatus: res.data.auth_status, authReason: res.data.auth_reason || '' })
    }).catch(() => {})
  },

  onSubmit() {
    if (this.data.submitting) return
    this.setData({ submitting: true })
    // MVP: mock ID photo upload; production should use wx.chooseMedia + upload + msgSecCheck
    api.post('/user/auth', {}).then(() => {
      wx.showToast({ title: 'Submitted, under review', icon: 'success' })
      this.loadStatus()
      app.refreshUser()
    }).catch(() => {}).finally(() => {
      this.setData({ submitting: false })
    })
  },
})

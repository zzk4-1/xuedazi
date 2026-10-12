const api = require('../../utils/api.js')
const app = getApp()

const AUTH_TEXT = {
  none: 'Not verified',
  pending: 'Under review',
  approved: 'Verified',
  rejected: 'Rejected',
}

Page({
  data: {
    user: null,
    authText: '',
    editingNick: false,
    nickname: '',
  },

  onShow() {
    app.ensureUser(user => {
      this.setData({ user, authText: AUTH_TEXT[user.auth_status] || user.auth_status })
    })
  },

  goSchool() {
    wx.navigateTo({ url: '/pages/school/school' })
  },

  goVerify() {
    wx.navigateTo({ url: '/pages/verify/verify' })
  },

  goAdmin() {
    wx.navigateTo({ url: '/pages/admin/admin' })
  },

  onEditNick() {
    this.setData({ editingNick: true, nickname: this.data.user.nickname || '' })
  },

  onNickInput(e) {
    this.setData({ nickname: e.detail.value })
  },

  onSaveNick() {
    const nickname = this.data.nickname.trim()
    if (!nickname) { wx.showToast({ title: 'Nickname cannot be empty', icon: 'none' }); return }
    api.post('/user/profile', { nickname }).then(() => {
      wx.showToast({ title: 'Saved', icon: 'success' })
      this.setData({ editingNick: false })
      app.refreshUser()
    }).catch(() => {})
  },
})

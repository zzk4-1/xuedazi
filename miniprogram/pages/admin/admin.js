const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    tab: 'auth', // auth / reports
    pendingAuth: [],
    reports: [],
  },

  onShow() {
    app.ensureUser(user => {
      if (user.role !== 1) {
        wx.showToast({ title: 'No admin permission', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 800)
        return
      }
      this.load()
    })
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.v }, () => this.load())
  },

  load() {
    if (this.data.tab === 'auth') {
      api.get('/admin/auth/pending').then(res => {
        this.setData({ pendingAuth: res.data || [] })
      }).catch(() => {})
    } else {
      api.get('/admin/reports').then(res => {
        this.setData({ reports: res.data || [] })
      }).catch(() => {})
    }
  },

  onAuthHandle(e) {
    const { openid, action } = e.currentTarget.dataset
    const doIt = (reason) => {
      api.post('/admin/auth/' + openid, { action, reason: reason || '' }).then(() => {
        wx.showToast({ title: 'Done', icon: 'success' })
        this.load()
      }).catch(() => {})
    }
    if (action === 'reject') {
      wx.showModal({
        title: 'Rejection reason',
        editable: true,
        placeholderText: 'e.g. ID photo unclear',
        success: r => { if (r.confirm) doIt(r.content) },
      })
    } else {
      wx.showModal({
        title: 'Confirm',
        content: 'Approve this student verification?',
        success: r => { if (r.confirm) doIt() },
      })
    }
  },

  onReportHandle(e) {
    const { id, type } = e.currentTarget.dataset
    const actions = type === 'card'
      ? [{ key: 'offline_card', label: 'Remove card' }, { key: 'reject', label: 'Dismiss report' }]
      : [{ key: 'ban_user', label: 'Ban user' }, { key: 'reject', label: 'Dismiss report' }]
    wx.showActionSheet({
      itemList: actions.map(a => a.label),
      success: res => {
        const action = actions[res.tapIndex].key
        api.post('/admin/reports/' + id, { action, result: 'Handled' }).then(() => {
          wx.showToast({ title: 'Done', icon: 'success' })
          this.load()
        }).catch(() => {})
      },
    })
  },
})

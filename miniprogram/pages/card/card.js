const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    id: 0,
    card: null,
    applyMsg: '',
    applying: false,
    receivedApps: [], // pending applications for creator
  },

  onLoad(options) {
    this.setData({ id: parseInt(options.id) })
  },

  onShow() {
    app.ensureUser(() => this.load())
  },

  load() {
    api.get('/cards/' + this.data.id).then(res => {
      const myOpenid = app.globalData.openid
      res.data.is_member = (res.data.members || []).some(m => m.openid === myOpenid)
      this.setData({ card: res.data })
      if (res.data.is_creator) this.loadReceivedApps()
    }).catch(() => {})
  },

  loadReceivedApps() {
    api.get('/applications').then(res => {
      const pending = (res.data.received || []).filter(a => a.status === 'pending' && a.card_id === this.data.id)
      this.setData({ receivedApps: pending })
    }).catch(() => {})
  },

  onApplyInput(e) {
    this.setData({ applyMsg: e.detail.value })
  },

  onApply() {
    if (this.data.applying) return
    const msg = this.data.applyMsg.trim()
    if (!msg) { wx.showToast({ title: 'Please write a message', icon: 'none' }); return }
    this.setData({ applying: true })
    api.post('/cards/' + this.data.id + '/apply', { message: msg }).then(() => {
      wx.showToast({ title: 'Application sent', icon: 'success' })
      this.setData({ applyMsg: '' })
      this.load()
    }).catch(() => {}).finally(() => {
      this.setData({ applying: false })
    })
  },

  onHandleApp(e) {
    const { id, action } = e.currentTarget.dataset
    wx.showModal({
      title: 'Confirm',
      content: action === 'approve' ? 'Approve this application?' : 'Reject this application?',
      confirmText: action === 'approve' ? 'Approve' : 'Reject',
      success: (r) => {
        if (!r.confirm) return
        api.post('/applications/' + id + '/handle', { action }).then(() => {
          wx.showToast({ title: 'Done', icon: 'success' })
          this.load()
        }).catch(() => {})
      },
    })
  },

  goTeam() {
    wx.navigateTo({ url: '/pages/team/team?id=' + this.data.id })
  },

  goReport() {
    wx.navigateTo({
      url: '/pages/report/report?target_type=card&target_id=' + this.data.id,
    })
  },
})

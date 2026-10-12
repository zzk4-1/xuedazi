const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    id: 0,
    card: null,
    checkins: [],
    streaks: {},
    checkedMap: {},
    myOpenid: '',
    todayChecked: false,
    text: '',
    submitting: false,
    today: '',
  },

  onLoad(options) {
    const d = new Date()
    const tz = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
    this.setData({ id: parseInt(options.id), today: tz })
  },

  onShow() {
    app.ensureUser(() => this.load())
  },

  load() {
    const myOpenid = app.globalData.openid
    this.setData({ myOpenid })
    api.get('/cards/' + this.data.id).then(res => {
      this.setData({ card: res.data })
    }).catch(() => {})
    api.get('/cards/' + this.data.id + '/checkins').then(res => {
      const list = res.data.checkins || []
      const checkedMap = {}
      list.forEach(c => { checkedMap[c.openid] = true })
      this.setData({
        checkins: list,
        streaks: res.data.streaks || {},
        checkedMap,
        todayChecked: !!checkedMap[myOpenid],
      })
    }).catch(() => {})
  },

  onInput(e) {
    this.setData({ text: e.detail.value })
  },

  onCheckin() {
    if (this.data.submitting) return
    const text = this.data.text.trim()
    if (!text) { wx.showToast({ title: 'Please write your check-in', icon: 'none' }); return }
    this.setData({ submitting: true })
    api.post('/cards/' + this.data.id + '/checkin', { text }).then(() => {
      wx.showToast({ title: 'Checked in', icon: 'success' })
      this.setData({ text: '' })
      this.load()
    }).catch(() => {}).finally(() => {
      this.setData({ submitting: false })
    })
  },

  goReport(e) {
    const openid = e.currentTarget.dataset.openid
    wx.navigateTo({ url: '/pages/report/report?target_type=user&target_id=' + openid })
  },
})

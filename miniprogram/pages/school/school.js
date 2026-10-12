const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    schools: [],
    current: '',
    loading: false,
  },

  onLoad() {
    api.get('/schools').then(res => {
      this.setData({ schools: res.data })
    })
    app.ensureUser(user => {
      this.setData({ current: user.school || '' })
    })
  },

  onSelect(e) {
    const school = e.currentTarget.dataset.name
    if (this.data.loading || school === this.data.current) return
    this.setData({ loading: true })
    api.post('/user/school', { school }).then(() => {
      wx.showToast({ title: 'School selected', icon: 'success' })
      return app.refreshUser()
    }).then(() => {
      setTimeout(() => wx.navigateBack(), 600)
    }).catch(() => {}).finally(() => {
      this.setData({ loading: false })
    })
  },
})

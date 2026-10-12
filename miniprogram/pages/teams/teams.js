const api = require('../../utils/api.js')
const app = getApp()

const STATUS_TEXT = {
  recruiting: 'Recruiting',
  full: 'Full',
  offline: 'Removed',
  finished: 'Finished',
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  expired: 'Expired',
}

Page({
  data: {
    tab: 'teams', // teams / apps
    teams: [],
    sent: [],
    received: [],
    loading: false,
  },

  onShow() {
    app.ensureUser(() => this.load())
  },

  switchTab(e) {
    this.setData({ tab: e.currentTarget.dataset.v })
  },

  load() {
    if (this.data.loading) return
    this.setData({ loading: true })
    Promise.all([
      api.get('/teams').catch(() => ({ data: [] })),
      api.get('/applications').catch(() => ({ data: { sent: [], received: [] } })),
    ]).then(([teams, apps]) => {
      const mapStatus = (list) => (list || []).map(item => ({
        ...item,
        statusText: STATUS_TEXT[item.status] || item.status,
      }))
      this.setData({
        teams: mapStatus(teams.data),
        sent: mapStatus(apps.data.sent),
        received: mapStatus(apps.data.received),
      })
    }).finally(() => this.setData({ loading: false }))
  },

  goTeam(e) {
    wx.navigateTo({ url: '/pages/team/team?id=' + e.currentTarget.dataset.id })
  },

  goCard(e) {
    wx.navigateTo({ url: '/pages/card/card?id=' + e.currentTarget.dataset.id })
  },

  onHandle(e) {
    const { id, action } = e.currentTarget.dataset
    wx.showModal({
      title: 'Confirm',
      content: action === 'approve' ? 'Approve this application?' : 'Reject this application?',
      confirmText: action === 'approve' ? 'Approve' : 'Reject',
      success: r => {
        if (!r.confirm) return
        api.post('/applications/' + id + '/handle', { action }).then(() => {
          wx.showToast({ title: 'Done', icon: 'success' })
          this.load()
        }).catch(() => {})
      },
    })
  },
})

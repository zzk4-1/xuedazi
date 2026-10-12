const api = require('../../utils/api.js')
const app = getApp()

const CATEGORIES = ['All', 'Grad School', 'Self-study', 'CET-4/6', 'IELTS/TOEFL', 'Thesis', 'Other']
const SLOTS = ['All', 'Early morning', 'Morning', 'Afternoon', 'Evening']

Page({
  data: {
    user: null,
    cards: [],
    loading: false,
    categories: CATEGORIES,
    slots: SLOTS,
    activeCategory: 'All',
    activeSlot: 'All',
  },

  onShow() {
    app.ensureUser(user => {
      this.setData({ user })
      if (!user.school) {
        wx.navigateTo({ url: '/pages/school/school' })
        return
      }
      this.loadCards()
    })
  },

  loadCards() {
    if (this.data.loading) return
    this.setData({ loading: true })
    const q = []
    if (this.data.activeCategory !== 'All') q.push('category=' + encodeURIComponent(this.data.activeCategory))
    if (this.data.activeSlot !== 'All') q.push('slots=' + encodeURIComponent(this.data.activeSlot))
    const path = '/cards' + (q.length ? '?' + q.join('&') : '')
    api.get(path).then(res => {
      const cards = (res.data || []).map(c => {
        let slots = c.slots
        try { slots = JSON.parse(c.slots).join(', ') } catch (e) {}
        return { ...c, slots }
      })
      this.setData({ cards })
    }).catch(() => {}).finally(() => {
      this.setData({ loading: false })
    })
  },

  onTapCategory(e) {
    this.setData({ activeCategory: e.currentTarget.dataset.v }, () => this.loadCards())
  },

  onTapSlot(e) {
    this.setData({ activeSlot: e.currentTarget.dataset.v }, () => this.loadCards())
  },

  goCard(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: '/pages/card/card?id=' + id })
  },
})

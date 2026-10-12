const api = require('../../utils/api.js')
const app = getApp()

const CATEGORIES = ['Grad School', 'Self-study', 'CET-4/6', 'IELTS/TOEFL', 'Thesis', 'Other']
const SLOT_OPTIONS = ['Early morning', 'Morning', 'Afternoon', 'Evening']

Page({
  data: {
    type: 'goal',
    title: '',
    category: CATEGORIES[0],
    categories: CATEGORIES,
    slotOptions: SLOT_OPTIONS,
    description: '',
    start_date: '',
    end_date: '',
    slots: [],
    place: '',
    target_count: 3,
    countOptions: ['2', '3', '4', '5', '6'],
    submitting: false,
  },

  onShow() {
    app.ensureUser(user => {
      if (!user.school) {
        wx.navigateTo({ url: '/pages/school/school' })
        return
      }
      if (user.auth_status !== 'approved') {
        wx.navigateTo({ url: '/pages/verify/verify' })
        return
      }
    })
  },

  onTypeChange(e) {
    this.setData({ type: e.detail.value === '0' ? 'goal' : 'place' })
  },

  onInput(e) {
    const key = e.currentTarget.dataset.key
    this.setData({ [key]: e.detail.value })
  },

  onPickCategory(e) {
    this.setData({ category: CATEGORIES[e.detail.value] })
  },

  onPickCount(e) {
    this.setData({ target_count: parseInt(e.detail.value) + 1 })
  },

  onPickDate(e) {
    const key = e.currentTarget.dataset.key // start / end
    const value = e.detail.value
    if (key === 'start') {
      if (this.data.end_date && value > this.data.end_date) {
        wx.showToast({ title: 'Start date must be before end date', icon: 'none' })
        return
      }
      this.setData({ start_date: value })
    } else {
      if (this.data.start_date && value < this.data.start_date) {
        wx.showToast({ title: 'End date must be after start date', icon: 'none' })
        return
      }
      this.setData({ end_date: value })
    }
  },

  toggleSlot(e) {
    const slot = e.currentTarget.dataset.v
    const list = this.data.slots
    const idx = list.indexOf(slot)
    if (idx >= 0) list.splice(idx, 1)
    else list.push(slot)
    this.setData({ slots: [...list] })
  },

  onSubmit() {
    if (this.data.submitting) return
    const d = this.data
    if (!d.title.trim()) { wx.showToast({ title: 'Please enter a title', icon: 'none' }); return }
    if (!d.start_date || !d.end_date) { wx.showToast({ title: 'Please select a period', icon: 'none' }); return }
    if (!d.slots.length) { wx.showToast({ title: 'Select at least one time slot', icon: 'none' }); return }
    if (!d.place.trim()) { wx.showToast({ title: 'Please enter a campus place', icon: 'none' }); return }

    this.setData({ submitting: true })
    api.post('/cards', {
      type: d.type,
      title: d.title.trim(),
      category: d.category,
      description: d.description.trim(),
      start_date: d.start_date,
      end_date: d.end_date,
      slots: d.slots,
      place: d.place.trim(),
      target_count: d.target_count,
    }).then(() => {
      wx.showToast({ title: 'Published', icon: 'success' })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/square/square' })
      }, 800)
    }).catch(() => {}).finally(() => {
      this.setData({ submitting: false })
    })
  },
})

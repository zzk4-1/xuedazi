const api = require('../../utils/api.js')

Page({
  data: {
    targetType: '',
    targetId: '',
    reasons: ['Fake identity', 'Harassment', 'Spam / ads', 'Inappropriate content', 'Other'],
    reason: '',
    detail: '',
    submitting: false,
  },

  onLoad(options) {
    this.setData({
      targetType: options.target_type || '',
      targetId: options.target_id || '',
    })
  },

  onPickReason(e) {
    this.setData({ reason: e.currentTarget.dataset.v })
  },

  onInput(e) {
    this.setData({ detail: e.detail.value })
  },

  onSubmit() {
    if (this.data.submitting) return
    if (!this.data.reason) { wx.showToast({ title: 'Please select a reason', icon: 'none' }); return }
    this.setData({ submitting: true })
    api.post('/reports', {
      target_type: this.data.targetType,
      target_id: this.data.targetId,
      reason: this.data.reason,
      detail: this.data.detail.trim(),
    }).then(() => {
      wx.showToast({ title: 'Report submitted', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 800)
    }).catch(() => {}).finally(() => {
      this.setData({ submitting: false })
    })
  },
})

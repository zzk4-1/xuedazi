const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    id: 0,
    messages: [],
    input: '',
    sending: false,
    myOpenid: '',
    peerName: 'Buddy',
  },

  onLoad(options) {
    this.setData({ id: parseInt(options.id), myOpenid: app.globalData.openid })
  },

  onShow() {
    this.load()
    // Polling for async message-style chat
    this._timer = setInterval(() => this.load(true), 5000)
  },

  onHide() {
    if (this._timer) clearInterval(this._timer)
  },

  onUnload() {
    if (this._timer) clearInterval(this._timer)
  },

  load(silent) {
    api.get('/chats/' + this.data.id, silent).then(res => {
      const peer = res.data.chat.user1_openid === app.globalData.openid ? res.data.chat.user2_openid : res.data.chat.user1_openid
      const peerMsg = (res.data.messages || []).find(m => m.sender_openid === peer)
      this.setData({
        messages: res.data.messages || [],
        peerName: peerMsg ? peerMsg.sender_nickname : 'Buddy',
      })
    }).catch(() => {})
  },

  onInput(e) {
    this.setData({ input: e.detail.value })
  },

  onSend() {
    if (this.data.sending) return
    const content = this.data.input.trim()
    if (!content) return
    this.setData({ sending: true })
    api.post('/chats/' + this.data.id + '/send', { content }).then(() => {
      this.setData({ input: '' })
      this.load(true)
    }).catch(() => {}).finally(() => {
      this.setData({ sending: false })
    })
  },

  goReport() {
    const msgs = this.data.messages
    const peer = msgs.find(m => m.sender_openid !== app.globalData.openid)
    if (peer) {
      wx.navigateTo({ url: '/pages/report/report?target_type=user&target_id=' + peer.sender_openid })
    }
  },
})

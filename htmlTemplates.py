css = '''
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #9d8152
    color: #FFFFFF;
    text-align: right;
    margin-left: auto;
    flex-direction: row-reverse;
}
.chat-message.bot {
    background-color: #43316d
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
  font-size: 18px;
}
'''

bot_template = '''
<div class="chat-message bot">
<img src="data:image/png;base64,{{URL}}" width="30" height="30" alt="" />
<div class="message">{{MSG}}</div>
</div>
'''

 

user_template = '''
<div class="chat-message user">
<img src="data:image/png;base64,{{URL}}" width="30" height="30" alt=""/>   
<div class="message">{{MSG}}</div>
</div>
'''
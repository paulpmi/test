
########################################################################################################
# The RWKV Language Model - https://github.com/BlinkDL/RWKV-LM
########################################################################################################

print('Loading...')
import numpy as np
import os, copy, types, gc, sys
os.environ['RWKV_JIT_ON'] = "1"

from src.model_run import RWKV_RNN
import torch
from src.utils import TOKENIZER
try:
    os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[1]
except:
    pass
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cuda.matmul.allow_tf32 = True
np.set_printoptions(precision=4, suppress=True, linewidth=200)

CHAT_LANG = 'English' # English Chinese

WORD_NAME = [
    "./src/trainers/RWKV-LM-LoRA/RWKV-v4neo/20B_tokenizer.json",
    "./src/trainers/RWKV-LM-LoRA/RWKV-v4neo/20B_tokenizer.json",
]  # [vocab, vocab] for Pile model
UNKNOWN_CHAR = None
tokenizer = TOKENIZER(WORD_NAME, UNKNOWN_CHAR=UNKNOWN_CHAR)


args = types.SimpleNamespace()
args.RUN_DEVICE = "cuda"  # 'cpu' (already very fast) // 'cuda'
args.FLOAT_MODE = "fp16" # fp32 (good for CPU) // fp16 (recommended for GPU) // bf16 (less accurate)
args.vocab_size = 50277
args.head_qk = 0
args.pre_ffn = 0
args.grad_cp = 0
args.my_pos_emb = 0

args.MODEL_NAME = './aimodels/RWKV-4-Raven-1B5-v12-Eng98%-Other2%-20230520-ctx4096'
args.n_layer = 24
args.n_embd = 2048
args.ctx_len = 8096 #1024

# Modify this to use LoRA models; lora_r = 0 will not use LoRA weights.
args.MODEL_LORA = './aimodels/rwkv-adapter-4/rwkv-0'
args.lora_r = 8
args.lora_alpha = 32

args.MERGERAVENMODELS = False

# args.MODEL_NAME = '/fsx/BlinkDL/HF-MODEL/rwkv-4-pile-7b/RWKV-4-Pile-7B-20221115-8047'
# args.n_layer = 32
# args.n_embd = 4096
# args.ctx_len = 1024

# args.MODEL_NAME = '/fsx/BlinkDL/HF-MODEL/rwkv-4-pile-3b/RWKV-4-Pile-3B-20221008-8023'
# args.n_layer = 32
# args.n_embd = 2560
# args.ctx_len = 1024

if CHAT_LANG == 'English':
    user = "Bob"
    bot = "Alice"
    interface = ":"

    # The following is a verbose and detailed conversation between an AI assistant called {bot}, and a human user called {user}. {bot} is intelligent, knowledgeable, wise and polite.
    # The following is a conversation between a highly knowledgeable and intelligent AI called {bot}, and a human called {user}. In the following interactions, {user} and {bot} converse in natural language, and {bot} do its best to answer {user}'s questions. {bot} is respectful, polite and inclusive. {bot} knows a lot, and always tells the truth.

    init_prompt = f'''
The following is a verbose and detailed conversation between an AI assistant called {bot}, and a human user called {user}. {bot} is intelligent, knowledgeable, wise and polite.

{user}{interface} french revolution what year

{bot}{interface} The French Revolution started in 1789, and lasted 10 years until 1799.

{user}{interface} 3+5=?

{bot}{interface} The answer is 8.

{user}{interface} guess i marry who ?

{bot}{interface} Only if you tell me more about yourself - what are your interests?

{user}{interface} solve for a: 9-a=2

{bot}{interface} The answer is a = 7, because 9 - 7 = 2.

{user}{interface} wat is lhc

{bot}{interface} LHC is a high-energy particle collider, built by CERN, and completed in 2008. They used it to confirm the existence of the Higgs boson in 2012.

'''

    init_prompt = f'''
The following is a verbose and detailed conversation between an AI assistant called {bot}, and a human user called {user}. {bot} is intelligent, knowledgeable, wise and polite.

{user}{interface} User Query: moen handshower
Act like a search engine. You will receive a user query and will have to provide the user with a list of relevant search results. The results will have to fit the user query but can also be varied while still catering to the user query.

{bot}{interface} Koolatron 700 gal. Pond Kit with 4-Piece Lighting;;Titan Lighting Copley Pond Collection 3-Light Satin Nickel Mini Pendant;;Titan Lighting Copley Pond Collection 6-Light Satin Nickel Mini Pendant;;Titan Lighting Copley Pond Collection 1-Light Satin Nickel Mini Pendant;;Moonrays Low Voltage 20-Watt Grey Outdoor Rock Spotlight;;Titan Lighting Copley Pond Collection 6-Light Satin Nickel Mini Pendant;;Titan Lighting Copley Pond Collection 3-Light Satin Nickel Mini Pendant;;Alpine 5 Sockets Lighting Cable 25 ft. and 14 Gauge;;Titan Lighting Copley Pond Collection 6-Light Satin Nickel Mini Pendant;;Titan Lighting Copley Pond Collection 1-Light Satin Nickel LED Mini Pendant;;Titan Lighting Copley Pond Collection 3-Light Satin Nickel Mini Pendant;;Titan Lighting Copley Pond Collection 6-Light Satin Nickel Mini Pendant;;Titan Lighting Copley Pond Collection 6-Light Satin Nickel Mini Pendant.

{user}{interface} The customer is looking for a smartphone with a large display and a long battery life.
Generate a product recommendation for a customer looking for a new smartphone.

{bot}{interface} Based on the customer's requirements, we recommend the Samsung Galaxy Note20 Ultra with a 6.9-inch display and a 4500mAh battery.

{user}{interface} i need a good suit for business.

{bot}{interface} Based on your interests and occupation, here are some good suit options to consider:The Tom Ford Suit Collection, Off-White Men's Slim-Homed Suit Collection, and Prada Made Men's Suit Collection which are gepected to fit your budget and preferences.

{user}{interface} I want to decorate my home, what's the best way to get started?

{bot}{interface} Start by identifying your personal style and the overall aesthetic you want to achieve in your home. Then, consider what types of furniture and decor you want to include, and make a plan for how you want to arrange them. It's also helpful to create a budget and stick to it to ensure that your decorating is affordable and sustainable.

{user}{interface} Does a brown lamp fit with the colors of a blue room ?

{bot}{interface} Brown and blue are complementary colors, meaning they are opposite each other on the color wheel. Therefore, the answer to the question is maybe, and it depends on the specific shades of brown and blue and personal preferences.

'''
    HELP_MSG = '''Commands:
say something --> chat with bot. use \\n for new line.
+alt --> alternate chat reply
+reset --> reset chat

+gen YOUR PROMPT --> free generation with any prompt. use \\n for new line.
+qa YOUR QUESTION --> free generation - ask any question (just ask the question). use \\n for new line.
+more --> continue last free generation (only for +gen / +qa)
+retry --> retry last free generation (only for +gen / +qa)

Now talk with the bot and enjoy. Remember to +reset periodically to clean up the bot's memory. Use RWKV-4 14B for best results.
This is not instruct-tuned for conversation yet, so don't expect good quality. Better use +gen for free generation.
'''
elif CHAT_LANG == 'Chinese':
    args.MODEL_NAME = '/fsx/BlinkDL/CODE/_PUBLIC_/RWKV-LM/RWKV-v4neo/7-run3z/rwkv-293'
    args.n_layer = 32
    args.n_embd = 4096
    args.ctx_len = 1024

    user = "Q"
    bot = "A"
    interface = ":"

    init_prompt = '''
Q: 企鹅会飞吗？

A: 企鹅是不会飞的。它们的翅膀主要用于游泳和平衡，而不是飞行。

Q: 西瓜是什么

A: 西瓜是一种常见的水果，是一种多年生蔓生藤本植物。西瓜的果实呈圆形或卵形，通常是绿色的，里面有红色或黄色的肉和很多的籽。西瓜味甜，多吃可以增加水分，是夏季非常受欢迎的水果之一。

'''
    HELP_MSG = '''指令:
直接输入内容 --> 和机器人聊天，用\\n代表换行
+alt --> 让机器人换个回答
+reset --> 重置对话

+gen 某某内容 --> 续写任何中英文内容，用\\n代表换行
+qa 某某问题 --> 问独立的问题（忽略上下文），用\\n代表换行
+more --> 继续 +gen / +qa 的回答
+retry --> 换个 +gen / +qa 的回答

现在可以输入内容和机器人聊天（注意它不怎么懂中文，它可能更懂英文）。请经常使用 +reset 重置机器人记忆。
'''

# Load Model

os.environ["RWKV_RUN_DEVICE"] = args.RUN_DEVICE
MODEL_NAME = args.MODEL_NAME

print(f'loading... {MODEL_NAME}')
model = RWKV_RNN(args)

model_tokens = []

current_state = None

########################################################################################################

def run_rnn(tokens, newline_adj = 0):
    global model_tokens, current_state
    for i in range(len(tokens)):
        model_tokens += [int(tokens[i])]
        if i == len(tokens) - 1:
            out, current_state = model.forward(model_tokens, current_state)
        else:
            current_state = model.forward(model_tokens, current_state, preprocess_only = True)
    
    # print(f'### model ###\n[{tokenizer.tokenizer.decode(model_tokens)}]')

    out[0] = -999999999  # disable <|endoftext|>
    out[187] += newline_adj
    # if newline_adj > 0:
    #     out[15] += newline_adj / 2 # '.'
    return out

all_state = {}
def save_all_stat(srv, name, last_out):
    n = f'{name}_{srv}'
    all_state[n] = {}
    all_state[n]['out'] = last_out
    all_state[n]['rnn'] = copy.deepcopy(current_state)
    all_state[n]['token'] = copy.deepcopy(model_tokens)

def load_all_stat(srv, name):
    global model_tokens, current_state
    n = f'{name}_{srv}'
    current_state = copy.deepcopy(all_state[n]['rnn'])
    model_tokens = copy.deepcopy(all_state[n]['token'])
    return all_state[n]['out']

########################################################################################################

# Run inference
print(f'\nRun prompt...')

out = run_rnn(tokenizer.tokenizer.encode(init_prompt))
gc.collect()
torch.cuda.empty_cache()

save_all_stat('', 'chat_init', out)

srv_list = ['dummy_server']
for s in srv_list:
    save_all_stat(s, 'chat', out)

print(f'### prompt ###\n[{tokenizer.tokenizer.decode(model_tokens, skip_special_tokens=True)}]\n')

def reply_msg(msg):
    print(f'{bot}{interface} {msg}\n')

def on_message(message):
    global model_tokens, current_state

    srv = 'dummy_server'

    msg = message.replace('\\n','\n').strip()
    if len(msg) > 3000:
        reply_msg('your message is too long (max 1000 tokens)')
        return

    x_temp = 1.8
    x_top_p = 0.8
    if ("-temp=" in msg):
        x_temp = float(msg.split("-temp=")[1].split(" ")[0])
        msg = msg.replace("-temp="+f'{x_temp:g}', "")
        # print(f"temp: {x_temp}")
    if ("-top_p=" in msg):
        x_top_p = float(msg.split("-top_p=")[1].split(" ")[0])
        msg = msg.replace("-top_p="+f'{x_top_p:g}', "")
        # print(f"top_p: {x_top_p}")
    if x_temp <= 0.2:
        x_temp = 0.2
    if x_temp >= 5:
        x_temp = 5
    if x_top_p <= 0:
        x_top_p = 0
    
    if msg == '+reset':
        out = load_all_stat('', 'chat_init')
        save_all_stat(srv, 'chat', out)
        reply_msg("Chat reset.")
        return

    elif msg[:5].lower() == '+gen ' or msg[:4].lower() == '+qa ' or msg.lower() == '+more' or msg.lower() == '+retry':

        if msg[:5].lower() == '+gen ':
            new = '\n' + msg[5:].strip()
            # print(f'### prompt ###\n[{new}]')
            current_state = None
            out = run_rnn(tokenizer.tokenizer.encode(new))
            save_all_stat(srv, 'gen_0', out)

        elif msg[:4].lower() == '+qa ':
            out = load_all_stat('', 'chat_init')

            real_msg = msg[4:].strip()
            new = f"{user}{interface} {real_msg}\n\n{bot}{interface}"
            # print(f'### qa ###\n[{new}]')
            
            out = run_rnn(tokenizer.tokenizer.encode(new))
            save_all_stat(srv, 'gen_0', out)

            # new = f"\nThe following is an excellent Q&A session consists of detailed and factual information.\n\nQ: What is 3+5?\nA: The answer is 8.\n\nQ: {msg[9:].strip()}\nA:"
            # print(f'### prompt ###\n[{new}]')
            # current_state = None
            # out = run_rnn(tokenizer.tokenizer.encode(new))
            # save_all_stat(srv, 'gen_0', out)

        elif msg.lower() == '+more':
            try:
                out = load_all_stat(srv, 'gen_1')
                save_all_stat(srv, 'gen_0', out)
            except:
                return

        elif msg.lower() == '+retry':
            try:
                out = load_all_stat(srv, 'gen_0')
            except:
                return

        begin = len(model_tokens)
        out_last = begin
        for i in range(500):
            token = tokenizer.sample_logits(
                out,
                model_tokens,
                args.ctx_len,
                temperature=x_temp,
                top_p_usual=x_top_p,
                top_p_newline=x_top_p,
            )
            if msg[:4].lower() == '+qa ':
                out = run_rnn([token], newline_adj=-1)
            else:
                out = run_rnn([token])
            
            xxx = tokenizer.tokenizer.decode(model_tokens[out_last:], skip_special_tokens=True)
            if '\ufffd' not in xxx:
                print(xxx, end='', flush=True)
                out_last = begin + i + 1
        print('\n')
        # send_msg = tokenizer.tokenizer.decode(model_tokens[begin:]).strip()
        # print(f'### send ###\n[{send_msg}]')
        # reply_msg(send_msg)
        save_all_stat(srv, 'gen_1', out)

    else:
        if msg.lower() == '+alt':
            try:
                out = load_all_stat(srv, 'chat_pre')
            except:
                return
        else:
            out = load_all_stat(srv, 'chat')
            new = f"{user}{interface} {msg}\n\n{bot}{interface}"
            # print(f'### add ###\n[{new}]')
            out = run_rnn(tokenizer.tokenizer.encode(new), newline_adj=-999999999)
            save_all_stat(srv, 'chat_pre', out)

        begin = len(model_tokens)
        out_last = begin
        print(f'{bot}{interface}', end='', flush=True)
        for i in range(999):
            if i <= 0:
                newline_adj = -999999999
            elif i <= 30:
                newline_adj = (i - 30) / 10
            elif i <= 130:
                newline_adj = 0
            else:
                newline_adj = (i - 200) * 0.25 # MUST END THE GENERATION
            token = tokenizer.sample_logits(
                out,
                model_tokens,
                args.ctx_len,
                temperature=x_temp,
                top_p_usual=x_top_p,
                top_p_newline=x_top_p,
            )
            out = run_rnn([token], newline_adj=newline_adj)

            xxx = tokenizer.tokenizer.decode(model_tokens[out_last:], skip_special_tokens=True)
            if '\ufffd' not in xxx:
                print(xxx, end='', flush=True)
                out_last = begin + i + 1
            
            send_msg = tokenizer.tokenizer.decode(model_tokens[begin:], skip_special_tokens=True)
            if '\n\n' in send_msg:
                send_msg = send_msg.strip()
                break
            
            # send_msg = tokenizer.tokenizer.decode(model_tokens[begin:]).strip()
            # if send_msg.endswith(f'{user}{interface}'): # warning: needs to fix state too !!!
            #     send_msg = send_msg[:-len(f'{user}{interface}')].strip()
            #     break
            # if send_msg.endswith(f'{bot}{interface}'):
            #     send_msg = send_msg[:-len(f'{bot}{interface}')].strip()
            #     break

        # print(f'{model_tokens}')
        # print(f'[{tokenizer.tokenizer.decode(model_tokens)}]')

        # print(f'### send ###\n[{send_msg}]')
        # reply_msg(send_msg)
        save_all_stat(srv, 'chat', out)

print(HELP_MSG)

while True:
    msg = input(f'{user}{interface} ')
    if len(msg.strip()) > 0:
        on_message(msg)
    else:
        print('Erorr: please say something')

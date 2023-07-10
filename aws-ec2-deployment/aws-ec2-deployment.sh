#este no es un script sh final, se debe correr cada comando independiente y cambiar los parametros/atributos de cada comando de acuerdo a como se vayan creando los servicios.

#1. Crear el archivo .pem del keypair
aws ec2 create-key-pair \
    --key-name videovigilancia-ec2-key-pair \
    --region us-west-2 \
    --key-type rsa \
    --key-format pem \
    --query "KeyMaterial" \
    --output text > videovigilancia-ec2-key-pair.pem

#2. Es necesario contar con una VPC
aws ec2 create-vpc \
    --cidr-block 192.168.0.0/28 \
    --tag-specification 'ResourceType=vpc,Tags=[{Key=Name,Value=videovigilancia-vpc}]' \
    --region us-west-2

#3. Se debe crear una subnet 
aws ec2 create-subnet \
    --vpc-id vpc-0cc411617c1e41366 \
    --region us-west-2 \
    --cidr-block 192.168.0.0/28 \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=videovigilancia-subnet}]'

#4. Crear un Internet Gateway para conducir la data entrante y saliente a Internet
aws ec2 create-internet-gateway \
    --region us-west-2 \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=videovigilancia-igw}]'

#5. Ahora el Internet Gatewat debe ser anexado al VPC creado previamente
aws ec2 attach-internet-gateway \
    --region us-west-2 \
    --internet-gateway-id igw-05d28735968731b88 \
    --vpc-id vpc-0cc411617c1e41366

#6. Crear tabla de ruta (ingress rule)
aws ec2 create-route-table \
    --region us-west-2 \
    --vpc-id vpc-0cc411617c1e41366

#7. Crea la ruta considerando la tabla de ruta creada previamente
aws ec2 create-route \
    --region us-west-2 \
    --route-table-id rtb-09e5670259d322a72 \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id igw-05d28735968731b88

#8. Asociar la ruta de tabla creada con la subnet creada
aws ec2 associate-route-table \
    --region us-west-2 \
    --route-table-id rtb-09e5670259d322a72 \
    --subnet-id subnet-017d8fa7a45af106a

#9. Es necesario habilitar la asignacion de IP publica a la subnet creada
aws ec2 modify-subnet-attribute \
    --region us-west-2 \
    --subnet-id subnet-017d8fa7a45af106a \
    --map-public-ip-on-launch

#10. Se debe crear un Security Group, necesario para poder permitir y configurar reglas de tráfico de entrada y salida para la instancia EC2
  aws ec2 create-security-group \
    --group-name videovigilancia-sg \
    --description "creation of security group for videovigilancia project" \
    --region us-west-2 \
    --vpc-id vpc-0cc411617c1e41366

#11. Cración de reglas para el SG para abrir los puertos 22 (ssh), 4000 y 5000
aws ec2 authorize-security-group-ingress \
    --group-id ${incluye-aqui-security-group} \
    --region us-west-2 \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id ${incluye-aqui-security-group} \
    --region us-west-2 \
    --protocol tcp \
    --port 4000 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id ${incluye-aqui-security-group} \
    --region us-west-2 \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0

#12. Validación de creación de reglas de entrada
aws ec2 describe-security-groups --group-ids ${incluye-aqui-security-group} --region us-west-2

#13. Creación de la instancia EC2, para encontrar el id de las imagenes de ubuntu
aws ec2 run-instances \
    --image-id ami-01f8a74810b880125 \
    --region us-west-2 \
    --count 1 \
    --instance-type t2.medium \
    --security-group-ids ${incluye-aqui-security-group} \
    --subnet-id subnet-017d8fa7a45af106a \
    --key-name videovigilancia-ec2-key-pair

#14. Ubicar una IP elastica del pool de AWS
aws ec2 allocate-address --region us-west-2

# En caso se desee saber la IP publica habilitada
aws ec2 describe-instances --instance-ids i-0a77b4a63b51ce184 \
    --region us-west-2 \
    --query 'Reservations[*].Instances[*].PublicIpAddress' \
    --output text

# Para saber la descripcion de la instancia creada
aws ec2 describe-instances \
    --instance-ids i-0a77b4a63b51ce184 \
    --region us-west-2

#15. Asociar la IP elastica (publica) habilitada a la instancia
aws ec2 associate-address \
    --region us-west-2 \
    --instance-id i-0a77b4a63b51ce184 \
    --allocation-id eipalloc-0ce7ef7cd4dbaa033

#16. Autorizar a mi IP para que se conecte a la instancia por el puerto 22
myip="$(dig +short myip.opendns.com @resolver1.opendns.com)"
aws ec2 authorize-security-group-ingress \
        --group-id ${incluye-aqui-security-group} \
        --region us-west-2 \
        --protocol tcp \
        --port 22 \
        --cidr "$myip/32" | jq '.'

#17. Conectarse por ssh es necesario darle los permisos al .pem file
chmod 400 ./videovigilancia-ec2-key-pair.pem

#18. Hacer ssh
ssh -i ./videovigilancia-ec2-key-pair.pem ubuntu@34.213.92.96


#19. Cuando se requiera darle de baja a la instancia:
aws ec2 terminate-instances --instance-ids i-0a77b4a63b51ce184


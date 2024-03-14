### Generate private key
``` 
openssl genrsa -out jwt-key 4096
```
### Generate public key
``` 
openssl rsa -in jwt-key -pubout > jwt-key.pub
```
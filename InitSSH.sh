#!/bin/bash
echo 'Add ssh keys'
sudo mkdir -p ~/.ssh
sudo echo ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDM9R46QxESf6lKFeap8KApskCxA5GGUHIsXK669CigDDAfzLBWJy8CYfvpqnkGeNgKVpe0khRffqOVhHwyAMEFtqYuBslftsfdOegmVJaJzGuoEobQJZDAd7+6jL1t2fjA6jN6L+nlSCnVh8/SDvFMF96eQZd4fkET8CFoyT2E5ZcIHekdKwAVuUXCOTrlMIlTp/2ScBZG3cNFVpBKd3X8NxjaV58qCoU6nqpLJDotCdmFDatGwkuHIghwPf17r/mYlkHPkilXz7/oFaZe0szu+hs2FFIvi0HDqbUqQUqOySp8yPgdqyTX3az4HdtbfPVJDw/14YPU4Dy/JeINalFj thongld@DESKTOP-L9AJ1QK >> ~/.ssh/authorized_keys
sudo echo ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAnX99ZHUi7XVBvqvv++s6a8HOoWqoWLvlyEOTi0hmGSi8yQdiyz9XJsrJNtWyxEzx9ZxWprWjk2LBRGdJ9VPWo/VbKB7Kepb9aYeG7nXg3hIUOYssMEGWXX4SghkuEpCGOLtjjTjCHb7PG7I6d5zZ2UhhVZ0sn5qphNPF8hR+tc0ewD9QmN+papk5+o9/ICynHWGoAuEge3PeAv4X2fmRAj3gTt401Xr++2tHaY3eNzvCwK8Y9rcBnYOm64t4hO0ykRP0A4+D9hnEeLEuWaNURrec1d/ncf+UN1Wbtxf51oV1dhDzTT7As8FcSHEQ6wc0yC7vqg5IupBFu5cWEcmTjQ== rsa-key-20160107 >> ~/.ssh/authorized_keys
echo 'Setup SSH'
sudo sed -ie 's/^Port.*$/Port 10022/' /etc/ssh/sshd_config
sudo sed -ie 's/^#*PasswordAuthentication .*$/PasswordAuthentication no/' /etc/ssh/sshd_config
echo 'restart SSH'
service sshd restart


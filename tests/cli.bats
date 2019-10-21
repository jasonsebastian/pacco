#!/usr/bin/env bats

@test "pacco remote list" {
  result="$(pacco remote list)"
  [ "${result}" == "[]" ]
}

@test "pacco remote add" {
  printf '\n' | pacco remote add local local
  result="$(pacco remote list)"
  [ "${result}" == "['local']" ]
  pacco remote remove local
}

@test "pacco remote remove" {
  printf '\n' | pacco remote add local local
  pacco remote remove local
  result="$(pacco remote list)"
  [ "${result}" == "[]" ]
}

@test "pacco remote list_default" {
  result="$(pacco remote list_default)"
  [ "${result}" == "[]" ]
}

@test "pacco remote set_default" {
  printf '\n' | pacco remote add local local
  pacco remote set_default local
  result="$(pacco remote list_default)"
  [ "${result}" == "['local']" ]
  pacco remote set_default
  pacco remote remove local
}

@test "pacco registry list" {
  printf '\n' | pacco remote add local local
  result="$(pacco registry list local)"
  [ "${result}" == "[]" ]
  pacco remote remove local
}

@test "pacco registry add" {
  printf '\n' | pacco remote add local local
  pacco registry add local openssl os,version,obfuscation
  result="$(pacco registry list local)"
  [ "${result}" == "['openssl']" ]
  pacco registry remove local openssl
  pacco remote remove local
}

@test "pacco registry remove" {
  printf '\n' | pacco remote add local local
  pacco registry add local openssl os,version,obfuscation
  pacco registry remove local openssl
  result="$(pacco registry list local)"
  [ "${result}" == "[]" ]
  pacco remote remove local
}

@test "pacco registry binaries" {
  printf '\n' | pacco remote add local local
  pacco registry add local openssl os,version,obfuscation
  result="$(pacco registry binaries local openssl)"
  [ "${result}" == "[]" ]
  pacco registry remove local openssl
  pacco remote remove local
}

@test "pacco binary upload" {
  printf '\n' | pacco remote add local local
  pacco registry add local openssl os,version,obfuscation
  mkdir openssl_upload_dir && touch openssl_upload_dir/sample.a
  pacco binary upload local openssl openssl_upload_dir os=android,version=2.1.0,obfuscation=obfuscated
  result="$(pacco registry binaries local openssl)"
  [ "${result}" == "[{'obfuscation': 'obfuscated', 'os': 'android', 'version': '2.1.0'}]" ]
  pacco binary remove local openssl os=android,version=2.1.0,obfuscation=obfuscated
  rm -rf openssl_upload_dir
  pacco registry remove local openssl
  pacco remote remove local
}

@test "pacco binary download" {
  printf '\n' | pacco remote add local local
  pacco registry add local openssl os,version,obfuscation
  mkdir openssl_upload_dir && touch openssl_upload_dir/sample.a
  pacco binary upload local openssl openssl_upload_dir os=android,version=2.1.0,obfuscation=obfuscated
  pacco binary download local openssl openssl_download_dir os=android,version=2.1.0,obfuscation=obfuscated
  result="$(ls openssl_download_dir)"
  [ "${result}" == "sample.a" ]
  pacco binary remove local openssl os=android,version=2.1.0,obfuscation=obfuscated
  rm -rf openssl_download_dir openssl_upload_dir
  pacco registry remove local openssl
  pacco remote remove local
}

@test "pacco binary remove" {
  printf '\n' | pacco remote add local local
  pacco registry add local openssl os,version,obfuscation
  mkdir openssl_upload_dir && touch openssl_upload_dir/sample.a
  pacco binary upload local openssl openssl_upload_dir os=android,version=2.1.0,obfuscation=obfuscated
  pacco binary remove local openssl os=android,version=2.1.0,obfuscation=obfuscated
  result="$(pacco registry binaries local openssl)"
  [ "${result}" == "[]" ]
  rm -rf openssl_upload_dir
  pacco registry remove local openssl
  pacco remote remove local
}
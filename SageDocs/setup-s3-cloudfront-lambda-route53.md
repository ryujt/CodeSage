# S3 버킷을 도메인 연결하여 클라우드 프론트로 배포하기

아래는 S3 정적 웹사이트 호스팅을 기반으로 한 React 애플리케이션을 CloudFront + Lambda@Edge로 연동하고, Route53 및 ACM을 사용해 test.com 도메인으로 HTTPS 연결까지 설정하는 전체 과정에 대한 가이드입니다.  
도메인은 `test.com` 이며, S3 버킷 이름도 동일하게 `test.com`으로 가정합니다. 인증서는 `test.com`과 `www.test.com`에 대해 us-east-1에서 발급합니다.  
아래 과정은 단계별로 AWS CLI 명령어와 설정 파일 예시를 차근차근 보여줍니다. 모든 코드 블록은 주석 없이, 누락 없이 작성합니다.

---

## 전체 개요

1. 사전 준비 및 도메인/호스팅존/React 빌드 준비  
2. ACM 인증서 발급 (test.com, www.test.com)  
3. S3 버킷 생성 및 정적 웹사이트 호스팅 설정  
4. React 빌드 파일 S3 업로드  
5. Lambda 함수 생성 및 버전 발행 (Lambda@Edge용)  
6. CloudFront 배포 생성 (ACM 인증서 사용) 및 Lambda@Edge 연결  
7. Route53 Alias 레코드 설정  
8. 검증

---

## 사전 준비

- AWS CLI 설치 및 자격증명 설정 완료  
- `test.com` 도메인을 Route53으로 이전 또는 호스팅존 생성 완료  
- React 애플리케이션 빌드 완료(`npm run build` 실행 후 build 디렉토리 준비)  
- us-east-1 리전으로 인증서 발급 (ACM) 예정

---

## 1단계: ACM 인증서 발급

아래 명령어를 통해 us-east-1 리전에 ACM 인증서를 요청합니다. 여기서 `test.com`과 `www.test.com` 두 도메인에 대한 인증서를 신청합니다. DNS 검증을 사용합니다.

```
aws acm request-certificate --domain-name test.com --subject-alternative-names www.test.com --validation-method DNS --region us-east-1
```

명령어 실행 결과로 ARN이 반환됩니다. 해당 인증서 ARN을 기록해둡니다. (예: `arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

이후 `aws acm describe-certificate --certificate-arn <위에서 얻은 ARN>` 명령으로 DNS 검증에 필요한 CNAME 레코드를 확인한 뒤 Route53에 해당 CNAME을 추가하여 검증을 완료합니다.

Route53에 CNAME 추가 예제(change-cname.json 작성):

```
{
  "Comment": "DNS validation for ACM",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "<검증에 필요한CNAME_이름>",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "<검증에 필요한CNAME_값>"
          }
        ]
      }
    }
  ]
}
```

호스팅존 ID 확인 후:

```
aws route53 change-resource-record-sets --hosted-zone-id <HOSTED_ZONE_ID> --change-batch file://change-cname.json
```

검증 완료 시 ACM 인증서 상태가 `ISSUED`로 변경됩니다.

---

## 2단계: S3 버킷 생성 및 정적 웹사이트 호스팅 설정

버킷 생성 (서울 리전 예시):

```
aws s3api create-bucket --bucket test.com --region ap-northeast-2 --create-bucket-configuration LocationConstraint=ap-northeast-2
```

정적 웹호스팅 설정용 `website-config.json` 파일 생성:

```
{
  "IndexDocument": {
    "Suffix": "index.html"
  },
  "ErrorDocument": {
    "Key": "index.html"
  }
}
```

설정 적용:

```
aws s3api put-bucket-website --bucket test.com --website-configuration file://website-config.json
```

React 빌드 파일 업로드:

```
aws s3 sync build/ s3://test.com
```

---

## 3단계: Lambda 함수 생성 및 버전 발행 (Lambda@Edge용)

`index.mjs` 파일 작성:

```
import path from 'path';
export const handler = async (event) => {
    const request = event.Records[0].cf.request;
    const uri = request.uri;
    if (!path.extname(uri)) {
        request.uri = '/index.html';
    }
    return request;
};
```

압축 및 함수 생성:

```
zip lambda.zip index.mjs
aws lambda create-function --function-name test-com-route --runtime nodejs22.x --handler index.handler --zip-file fileb://lambda.zip --role arn:aws:iam::<ACCOUNT_ID>:role/lambda-full --region us-east-1 --architectures x86_64
```

버전 발행:

```
aws lambda publish-version --function-name test-com-route --region us-east-1
```

발행된 버전 ARN 확인 (예: `arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:test-com-route:1`)

---

## 4단계: CloudFront 배포 생성 (ACM 인증서 사용)

`cloudfront-config.json` 파일 작성:

```
{
  "CallerReference": "test-com-cf-distribution",
  "Aliases": {
    "Quantity": 1,
    "Items": ["test.com"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "testComS3Origin",
        "DomainName": "test.com.s3-website.ap-northeast-2.amazonaws.com",
        "OriginPath": "",
        "CustomHeaders": {
          "Quantity": 0
        },
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only",
          "OriginSslProtocols": {
            "Quantity": 1,
            "Items": ["TLSv1.2"]
          }
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "testComS3Origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET","HEAD"]
    },
    "LambdaFunctionAssociations": {
      "Quantity": 1,
      "Items": [
        {
          "LambdaFunctionARN": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:test-com-route:1",
          "EventType": "origin-request",
          "IncludeBody": false
        }
      ]
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      },
      "Headers": {
        "Quantity": 0
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "Comment": "Distribution for test.com",
  "Enabled": true,
  "ViewerCertificate": {
    "ACMCertificateArn": "<ACM_CERTIFICATE_ARN>",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021",
    "CertificateSource": "acm"
  }
}
```

생성:

```
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

명령어 성공 시 CloudFront 도메인 이름(예: `dxxxxxxxxxx.cloudfront.net`)이 반환됩니다.

---

## 5단계: Route53 Alias 레코드 설정

`change-batch.json` 파일 작성:

```
{
  "Comment": "Create alias for test.com",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "test.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDT1GFXG3Q2C",
          "DNSName": "dxxxxxxxxxx.cloudfront.net",
          "EvaluateTargetHealth": false
        }
      }
    }
  ]
}
```

HOSTED_ZONE_ID를 찾은 후 (예: `Z0837536231AZ4TI95ON0`):

```
aws route53 change-resource-record-sets --hosted-zone-id Z0837536231AZ4TI95ON0 --change-batch file://change-batch.json
```

---

## 6단계: 검증

DNS 전파 후 `https://test.com` 접속 시 React 앱이 정상적으로 서비스되고, SPA 라우팅이 Lambda@Edge를 통해 동작하는지 확인합니다.


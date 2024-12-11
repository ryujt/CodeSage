# S3 버킷을 도메인 연결하여 클라우드 프론트로 배포하기

아래는 S3를 이용한 정적 웹사이트 호스팅, 이를 CloudFront + Lambda@Edge로 연동하고, Route53을 통해 커스텀 도메인을 연결하는 전체적인 가이드입니다.  
각 단계별로 필요한 AWS CLI 명령어와 설정 파일 예시를 순서대로 제시합니다. 코드 블록 내의 내용은 주석 없이 전부 보여주며, 누락 없이 작성합니다.

## 전체 개요

1. S3 버킷 생성 및 정적 웹 호스팅 설정  
2. React 애플리케이션 빌드 파일 S3 업로드  
3. Lambda 함수 생성 및 버전 발행 (Lambda@Edge용)  
4. CloudFront 배포 생성 및 Lambda@Edge 연결  
5. Route53에 Alias 레코드 설정

## 사전 준비

- AWS CLI 설치 및 프로필/자격증명 설정 완료
- 도메인(himytv.co.kr) Route53 호스팅 존 등록 완료
- ACM 인증서(us-east-1 리전에 요청 및 발급)
- React 빌드 완료(`npm run build` 등)

## 단계별 가이드

### 1. S3 버킷 생성 및 정적 웹사이트 호스팅 설정

```
aws s3api create-bucket --bucket room.himytv.com --region ap-northeast-2 --create-bucket-configuration LocationConstraint=ap-northeast-2
```

`website-config.json` 파일 생성:

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

```
aws s3api put-bucket-website --bucket room.himytv.com --website-configuration file://website-config.json
```

React 빌드 결과물 업로드:

```
aws s3 sync build/ s3://room.himytv.com
```

### 2. Lambda 함수 준비 및 버전 발행

`index.mjs` (Lambda 함수 코드, Node.js 22.x 예제):

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

ZIP 생성 후 Lambda 함수 생성:

```
zip lambda.zip index.mjs
aws lambda create-function --function-name room-himytv-route --runtime nodejs22.x --handler index.handler --zip-file fileb://lambda.zip --role arn:aws:iam::577992228379:role/lambda-full --region us-east-1 --architectures x86_64
```

버전 발행:

```
aws lambda publish-version --function-name room-himytv-route --region us-east-1
```

생성된 버전의 ARN 확인 (예: `arn:aws:lambda:us-east-1:577992228379:function:room-himytv-route:2`)

### 3. CloudFront 배포 설정

`cloudfront-config.json` 파일 생성:

```
{
  "CallerReference": "room-himytv-cf-distribution",
  "Aliases": {
    "Quantity": 1,
    "Items": ["room.himytv.co.kr"]
  },
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "roomhimytvS3Origin",
        "DomainName": "room.himytv.com.s3-website.ap-northeast-2.amazonaws.com",
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
    "TargetOriginId": "roomhimytvS3Origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET","HEAD"]
    },
    "LambdaFunctionAssociations": {
      "Quantity": 1,
      "Items": [
        {
          "LambdaFunctionARN": "arn:aws:lambda:us-east-1:577992228379:function:room-himytv-route:2",
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
  "Comment": "Distribution for room.himytv.co.kr",
  "Enabled": true,
  "ViewerCertificate": {
    "ACMCertificateArn": "arn:aws:acm:us-east-1:577992228379:certificate/62072504-c0de-4263-aca4-340357c07932",
    "SSLSupportMethod": "sni-only",
    "MinimumProtocolVersion": "TLSv1.2_2021",
    "CertificateSource": "acm"
  }
}
```

```
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

생성된 CloudFront 도메인 (예: `d3dqrgj95ab88b.cloudfront.net`) 확인

### 4. Route53 Alias 레코드 설정

`change-batch.json` 파일 생성:

```
{
  "Comment": "Create alias for room.himytv.co.kr",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "room.himytv.co.kr",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDT1GFXG3Q2C",
          "DNSName": "d3dqrgj95ab88b.cloudfront.net",
          "EvaluateTargetHealth": false
        }
      }
    }
  ]
}
```

호스팅존 ID 확인 후 (예: `Z0837536231AZ4TI95ON0`):

```
aws route53 change-resource-record-sets --hosted-zone-id Z0837536231AZ4TI95ON0 --change-batch file://change-batch.json
```

### 5. 검증

DNS 전파 후 `https://room.himytv.co.kr` 접속 시 React 앱이 정상적으로 서비스되는지 확인합니다.

---

위 단계들을 순서대로 수행하면 S3에 React 빌드 결과물을 업로드하고, CloudFront + Lambda@Edge로 SPA 라우팅을 지원하며, Route53을 통해 커스텀 도메인으로 서비스하는 구성이 완성됩니다.
<h1>AWS Lambda Function using Python Flask</h1>

<h4>Steps to create the environment and use the code</h4>

Step-1: Clone the repository - git clone https://github.com/shyam454/Flask_AWS.git

Step-2: Create Virtual Environment
            cd Flask_AWS
            pip install virtualenv
            virtualenv -p C:\Python36\python.exe env      # In place of C:\Python36\python.exe, give your python executable location

Step-3: Activate the Virtual Environment
            cd \env\scripts
            activate.bat        # Run this bat file if you are using a windows machine
            source .\activate   # Run this command if you are using Linux or Mac

Step-4: The above step activates Virtual Environment. You should be seeing (env) at the start of your command line. Now install the Python libraries and other dependencies 
            pip install Flask
            pip install aws_lambda_wsgi
            serverless create -t aws-python3
            npm install serverless-wsgi
            npm install serverless-python-requirements   
            pip freeze > requirements.txt                # Having a requirements file will help serverless to install all the Python dependency libraries in the Lambda
            pip install boto3                            # Python AWS SDK

Step-5: Deploy on AWS
            serverless deploy



<h4>Endpoints that are included in this Python Flask Lambda</h4>
Device Registration
Device Shadow
Access S3Bucket

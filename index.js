exports.handler = async (event, context) => {
  // Your Lambda function code here
  return {
    statusCode: 200,
    body: JSON.stringify('Hello from Lambda!'),
  };
};
import { NextRequest, NextResponse } from 'next/server';
import { Client } from 'minio';
import formidable from 'formidable';
import fs from 'fs';

// Initialize MinIO client
const minioClient = new Client({
  endPoint: process.env.MINIO_ENDPOINT || 'localhost',
  port: parseInt(process.env.MINIO_PORT || '9001'),
  useSSL: process.env.MINIO_USE_SSL === 'true',
  accessKey: process.env.MINIO_ACCESS_KEY!,
  secretKey: process.env.MINIO_SECRET_KEY!,
});

export const config = {
  api: {
    bodyParser: false,
  },
};

export async function POST(req: NextRequest) {
  // Check if MinIO client initialized correctly
  if (!minioClient) {
    console.error('MinIO client is not initialized correctly.');
    return NextResponse.json({ message: 'MinIO client error' }, { status: 500 });
  }

  // Parse the request using formidable
  const form = new formidable.IncomingForm();

  form.parse(req as any, async (err, fields, files) => {
    if (err) {
      console.error('Form parsing error:', err);
      return NextResponse.json({ message: 'File parsing error' }, { status: 500 });
    }
    if (files.file) {
    const file = files.file[0];
    const fileStream = fs.createReadStream(file.filepath);
    const fileName = file.originalFilename;

    if (fileName === null){
        throw new Error('File name is null');
      }

    try {
      const bucketName = process.env.MINIO_BUCKET_NAME || 'default-bucket-name';
      await minioClient.putObject(bucketName, fileName, fileStream);
      console.log('File uploaded successfully');
      return NextResponse.json({ message: 'File uploaded successfully' }, { status: 200 });
    } catch (err) {
      const error = err as Error;
      return NextResponse.json({ message: 'MinIO upload error', error: error.message }, { status: 500 });
    }
  }});

  // Ensure to send a response, or the API will stall
  return NextResponse.json({ message: 'Request processed' });
}

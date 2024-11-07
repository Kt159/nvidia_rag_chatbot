// import { Client } from 'minio';
import { NextRequest, NextResponse } from 'next/server';

const Minio = require('minio');
const [endPoint, port] = (process.env.MINIO_ENDPOINT || 'localhost:9000').split(':');

// Create a MinIO client
const minioClient = new Minio.Client({
    endPoint: endPoint,      
    port: parseInt(port),    
    useSSL: false,                             
    accessKey: process.env.MINIO_ACCESS_KEY,   // MinIO access key
    secretKey: process.env.MINIO_SECRET_KEY    // MinIO secret key
});

const bucketName: string = process.env.MINIO_BUCKET_NAME || 'default-bucket-name';

// POST: Handle file upload to MinIO
export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json({ message: 'No file uploaded' }, { status: 400 });
    }

    const fileBuffer = await file.arrayBuffer();
    const fileName = file.name;

    await minioClient.putObject(bucketName, fileName, Buffer.from(fileBuffer));

    return NextResponse.json({ message: 'File uploaded successfully', file_name: fileName }, { status: 200 });
  } catch (error) {
    console.error('Error uploading file:', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ message: 'MinIO upload error', error: errorMessage }, { status: 500 });
  }
}

// GET: List all objects in the MinIO bucket
export async function GET() {
  try {
    const objects = await minioClient.listObjects(bucketName, '', true);
    const documents: string[] = [];

    for await (const obj of objects) {
      documents.push(obj.name);
    }

    return NextResponse.json(documents);
  } catch (error) {
    const err = error as Error;
    return NextResponse.json({ message: 'Error fetching documents', error: err.message }, { status: 500 });
  }
}

// DELETE: Delete a specific document from MinIO
export async function DELETE(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const fileName = searchParams.get('filename');

  if (!fileName) {
    return NextResponse.json({ message: 'Filename is required' }, { status: 400 });
  }

  try {
    await minioClient.removeObject(bucketName, fileName);
    return NextResponse.json({ message: 'Document deleted successfully' }, { status: 200 });
  } catch (error) {
    const err = error as Error;
    return NextResponse.json({ message: 'Error deleting document', error: err.message }, { status: 500 });
  }
}

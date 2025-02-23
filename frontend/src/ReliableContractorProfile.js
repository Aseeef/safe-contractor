import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserCircle } from '@fortawesome/free-solid-svg-icons';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faCheckSquare, faSquare } from '@fortawesome/free-regular-svg-icons';
import './ContractorProfile.css'; // Import the CSS file

library.add(faCheckSquare, faSquare);

const ReliableContractorProfile = () => {
    const contractorData = {
        name: 'John Doe',
        id: '12345',
        location: 'Anytown, USA',
        rating: 4.5,
        yearsInBusiness: 10,
    };

    const pastProjects = [
        { location: 'Suburbia', name: 'House Renovation', amount: '$10,000', complete: true },
        { location: 'Downtown', name: 'Office Remodel', amount: '$25,000', complete: false },
        { location: 'Rural', name: 'Barn Restoration', amount: '$15,000', complete: true },
    ];

    const reviews = [
        'Excellent work, highly recommended!',
        'Professional and on time.',
        'Great communication throughout the project.',
    ];

    return (
        <div className="contractor-profile-container">
            <div className="header">
                <h1>Reliable Contractor</h1>
                <FontAwesomeIcon icon={faUserCircle} size="3x" className="profile-icon" />
            </div>
            <div className="info">
                <p><strong>Name:</strong> {contractorData.name}</p>
                <p><strong>ID:</strong> {contractorData.id}</p>
                <p><strong>Location:</strong> {contractorData.location}</p>
                <p><strong>Rating:</strong> {contractorData.rating}</p>
                <p><strong>Years in Business:</strong> {contractorData.yearsInBusiness}</p>
            </div>
            <h3>Past Projects</h3>
            <div className="past-projects">
                <table className="projects-table">
                    <thead>
                        <tr>
                            <th>Location</th>
                            <th>Name</th>
                            <th>Amount</th>
                            <th>Complete?</th>
                        </tr>
                    </thead>
                    <tbody>
                        {pastProjects.map((project, index) => (
                            <tr key={index}>
                                <td>{project.location}</td>
                                <td>{project.name}</td>
                                <td>{project.amount}</td>
                                <td>
                                    {project.complete ?
                                        <FontAwesomeIcon icon={['far', 'check-square']} style={{ color: '#28a745' }} /> :
                                        <FontAwesomeIcon icon={['far', 'square']} style={{ color: '#dc3545' }} />}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="reviews">
                <h3>Reviews:</h3>
                <ul>
                    {reviews.map((review, index) => (
                        <li key={index}>{review}</li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default ReliableContractorProfile;
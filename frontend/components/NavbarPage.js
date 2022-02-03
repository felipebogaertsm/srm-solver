// -* - coding: utf - 8 -* -
// Author: Felipe Bogaerts de Mattos
// Contact me at felipe.bogaerts@engenharia.ufjf.br.
// This program is free software: you can redistribute it and / or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, version 3.

// Components:
import Navbar from '../components/Navbar'

function NavbarPage({ children }) {
    return (
        <div>
            <Navbar />

            <div>
                {children}
            </div>
        </div>
    )
}

export default NavbarPage
